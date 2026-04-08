from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from jobs.models import Job, JobCategory, WorkMode, EmploymentType

from applications.forms import ApplicationForm, ApplicationStatusForm
from applications.models import Application
from jobs.forms import JobForm
from jobs.models import Job, JobCategory
from users.forms import RegisterForm
from users.models import User


def has_admin_permission(user):
    return user.is_authenticated and (
        getattr(user, 'role', None) == 'admin' or user.is_staff or user.is_superuser
    )


def _get_safe_next_url(request, default='dashboard'):
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return next_url
    return default


def home(request):
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    mode = request.GET.get('mode', '').strip()
    category_id = request.GET.get('category', '').strip()
    employment = request.GET.get('employment', '').strip()
    salary_type = request.GET.get('salary_type', '').strip()
    city = request.GET.get('city', '').strip()

    today = timezone.localdate()
    jobs = Job.objects.select_related('employer').prefetch_related('categories').all()
    if query:
        jobs = jobs.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(required_skills__icontains=query)
            | Q(employer__username__icontains=query)
        )
    if status == 'open':
        jobs = jobs.filter(status='open').filter(Q(deadline__isnull=True) | Q(deadline__gte=today))
    elif status == 'expired':
        jobs = jobs.filter(status='open', deadline__lt=today)
    elif status in {'in_progress', 'completed', 'cancelled'}:
        jobs = jobs.filter(status=status)
    if mode:
        jobs = jobs.filter(work_mode_obj__code=mode)
    if category_id.isdigit():
        jobs = jobs.filter(categories__id=int(category_id))
    if employment:
        jobs = jobs.filter(employment_type_obj__code=employment)
    if salary_type in {'negotiable', 'range', 'fixed'}:
        jobs = jobs.filter(salary_type=salary_type)
    if city:
        jobs = jobs.filter(city__icontains=city)

    paginator = Paginator(jobs.distinct(), 9)
    page_obj = paginator.get_page(request.GET.get('page'))

    stats = {
        'jobs': Job.objects.count(),
        'open_jobs': Job.objects.filter(status='open').filter(
            Q(deadline__isnull=True) | Q(deadline__gte=today)
        ).count(),
        'students': User.objects.filter(role='student').count(),
        'employers': User.objects.filter(role='employer').count(),
    }

    context = {
        'page_obj': page_obj,
        'query': query,
        'status': status,
        'mode': mode,
        'category_id': category_id,
        'employment': employment,
        'salary_type': salary_type,
        'city': city,
        'categories': JobCategory.objects.all(),
        'stats': stats,
        'work_modes': WorkMode.objects.all(),
        'employment_types': EmploymentType.objects.all(),
    }
    return render(request, 'home.html', context)


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Chào mừng! Tài khoản của bạn đã được tạo thành công.')
            return redirect('home')
    else:
        form = RegisterForm()

    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, 'Đăng nhập thành công.')
            return redirect('home')
        messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng.')
    else:
        form = AuthenticationForm(request)

    return render(request, 'auth/login.html', {'form': form})


@login_required
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.info(request, 'Bạn đã đăng xuất.')
        return redirect('home')
    return HttpResponseForbidden('Đăng xuất cần sử dụng POST.')


@login_required
def dashboard(request):
    user = request.user
    context = {'user': user}

    if user.role == 'student':
        context['applications'] = (
            Application.objects.select_related('job')
            .filter(student=user)
            .order_by('-applied_at')[:8]
        )
        context['recommended_jobs'] = (
            Job.objects.filter(status='open')
            .filter(Q(deadline__isnull=True) | Q(deadline__gte=timezone.localdate()))
            .exclude(applications__student=user)
            .prefetch_related('categories')[:8]
        )

    elif user.role == 'employer':
        context['posted_jobs'] = (
            Job.objects.filter(employer=user)
            .annotate(application_count=Count('applications'))
            .prefetch_related('categories')[:8]
        )
        context['recent_applications'] = (
            Application.objects.select_related('student', 'job')
            .filter(job__employer=user)
            .order_by('-applied_at')[:10]
        )

    else:
        context['admin_metrics'] = {
            'users': User.objects.count(),
            'jobs': Job.objects.count(),
            'applications': Application.objects.count(),
            'open_jobs': Job.objects.filter(status='open').filter(
                Q(deadline__isnull=True) | Q(deadline__gte=timezone.localdate())
            ).count(),
        }
        context['recent_jobs'] = Job.objects.select_related('employer').prefetch_related(
            'categories'
        )[:8]
        context['recent_applications'] = Application.objects.select_related('student', 'job')[:8]

    return render(request, 'dashboard.html', context)


def job_detail(request, pk):
    job = get_object_or_404(Job.objects.select_related('employer').prefetch_related('categories'), pk=pk)
    can_edit = request.user.is_authenticated and (
        request.user == job.employer or has_admin_permission(request.user)
    )
    can_apply = request.user.is_authenticated and request.user.role == 'student'

    existing_application = None
    apply_form = None
    if can_apply:
        existing_application = Application.objects.filter(student=request.user, job=job).first()
        if not existing_application and job.is_receiving_applications:
            apply_form = ApplicationForm(user=request.user)

    context = {
        'job': job,
        'can_edit': can_edit,
        'can_apply': can_apply,
        'existing_application': existing_application,
        'apply_form': apply_form,
        'applications_count': job.applications.count(),
    }
    return render(request, 'jobs/job_detail.html', context)


@login_required
def job_create(request):
    if request.user.role != 'employer' and not has_admin_permission(request.user):
        messages.error(request, 'Chỉ tài khoản nhà tuyển dụng mới có thể đăng việc.')
        return redirect('home')

    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.employer = request.user
            job.save()
            form.save_m2m()
            messages.success(request, 'Đăng việc thành công.')
            return redirect('job_detail', pk=job.pk)
    else:
        form = JobForm()

    return render(request, 'jobs/job_form.html', {'form': form, 'mode': 'create'})


@login_required
def job_edit(request, pk):
    job = get_object_or_404(Job, pk=pk)
    if request.user != job.employer and not has_admin_permission(request.user):
        return HttpResponseForbidden('Bạn không có quyền sửa việc này.')

    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cập nhật việc thành công.')
            return redirect('job_detail', pk=job.pk)
    else:
        form = JobForm(instance=job)

    return render(request, 'jobs/job_form.html', {'form': form, 'mode': 'edit', 'job': job})


@login_required
def job_delete(request, pk):
    job = get_object_or_404(Job, pk=pk)
    if request.user != job.employer and not has_admin_permission(request.user):
        return HttpResponseForbidden('Bạn không có quyền xóa việc này.')

    next_url = _get_safe_next_url(request, default='dashboard')
    if request.method == 'POST':
        job.delete()
        messages.success(request, 'Đã xóa việc thành công.')
        return redirect(next_url)

    return render(request, 'jobs/job_delete_confirm.html', {'job': job, 'next_url': next_url})


@login_required
def apply_job(request, pk):
    if request.user.role != 'student':
        messages.error(request, 'Chỉ tài khoản sinh viên mới có thể ứng tuyển.')
        return redirect('job_detail', pk=pk)

    job = get_object_or_404(Job, pk=pk)
    if not job.is_receiving_applications:
        messages.error(request, 'Việc này hiện không nhận ứng tuyển.')
        return redirect('job_detail', pk=pk)

    if Application.objects.filter(student=request.user, job=job).exists():
        messages.info(request, 'Bạn đã ứng tuyển việc này rồi.')
        return redirect('job_detail', pk=pk)

    form = ApplicationForm(request.POST, request.FILES, user=request.user)
    if form.is_valid():
        application = form.save(commit=False)
        application.student = request.user
        application.job = job
        if not application.cv_file and request.user.default_cv:
            application.cv_file = request.user.default_cv
        application.save()
        messages.success(request, 'Ứng tuyển thành công.')
    else:
        messages.error(request, 'Vui lòng sửa các lỗi trong đơn ứng tuyển.')

    return redirect('job_detail', pk=pk)


@login_required
def applications_view(request):
    user = request.user
    if user.role == 'student':
        applications = Application.objects.select_related('job', 'job__employer').filter(
            student=user
        )
    elif user.role == 'employer':
        applications = Application.objects.select_related('job', 'student').filter(
            job__employer=user
        )
    else:
        applications = Application.objects.select_related('job', 'student', 'job__employer').all()

    return render(
        request,
        'applications/application_list.html',
        {'applications': applications, 'status_form': ApplicationStatusForm()},
    )


@login_required
def update_application_status(request, pk):
    application = get_object_or_404(Application.objects.select_related('job'), pk=pk)
    if request.user != application.job.employer and not has_admin_permission(request.user):
        return HttpResponseForbidden('Bạn không có quyền cập nhật đơn ứng tuyển này.')

    if request.method == 'POST':
        form = ApplicationStatusForm(request.POST, instance=application)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cập nhật trạng thái đơn ứng tuyển thành công.')
        else:
            messages.error(request, 'Trạng thái cập nhật không hợp lệ.')

    return redirect('application_list')

