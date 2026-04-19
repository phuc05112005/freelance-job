from datetime import date

from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
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
from users.forms import AccountPasswordChangeForm, ProfileUpdateForm, RegisterForm
from users.models import User


def has_admin_permission(user):
    return user.is_authenticated and (
        getattr(user, 'role', None) == 'admin' or user.is_staff or user.is_superuser
    )


def _get_safe_next_url(request, default='home'):
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return next_url
    return default


def _parse_date_param(raw_value):
    if not raw_value:
        return None
    try:
        return date.fromisoformat(raw_value)
    except ValueError:
        return None


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
        return redirect('home')

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
        return redirect('home')

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
def account_profile(request):
    profile_form = ProfileUpdateForm(instance=request.user)
    password_form = AccountPasswordChangeForm(user=request.user)

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'profile':
            profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Cập nhật thông tin tài khoản thành công.')
                return redirect('account_profile')
            messages.error(request, 'Vui lòng sửa các lỗi trong thông tin tài khoản.')
        elif form_type == 'password':
            password_form = AccountPasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Đổi mật khẩu thành công.')
                return redirect('account_profile')
            messages.error(request, 'Vui lòng kiểm tra lại thông tin mật khẩu.')

    return render(
        request,
        'account/profile.html',
        {'profile_form': profile_form, 'password_form': password_form},
    )

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

    next_url = _get_safe_next_url(request, default='home')
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
        if not application.candidate_email:
            application.candidate_email = request.user.email or ''
        if not application.candidate_phone:
            application.candidate_phone = request.user.phone or ''
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
    status_choices = (
        ('pending', 'Chờ duyệt'),
        ('accepted', 'Đã chấp nhận'),
        ('rejected', 'Đã từ chối'),
    )
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    job_id = request.GET.get('job', '').strip()
    from_date_raw = request.GET.get('from_date', '').strip()
    to_date_raw = request.GET.get('to_date', '').strip()
    sort = request.GET.get('sort', '').strip()

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

    base_applications = applications

    status_totals = base_applications.aggregate(
        all=Count('id'),
        pending=Count('id', filter=Q(status='pending')),
        accepted=Count('id', filter=Q(status='accepted')),
        rejected=Count('id', filter=Q(status='rejected')),
    )

    if query:
        applications = applications.filter(
            Q(job__title__icontains=query)
            | Q(student__username__icontains=query)
            | Q(candidate_email__icontains=query)
            | Q(candidate_phone__icontains=query)
        )

    if status in {code for code, _ in status_choices}:
        applications = applications.filter(status=status)

    if job_id.isdigit():
        applications = applications.filter(job_id=int(job_id))
    else:
        job_id = ''

    from_date = _parse_date_param(from_date_raw)
    to_date = _parse_date_param(to_date_raw)
    if from_date:
        applications = applications.filter(applied_at__date__gte=from_date)
    if to_date:
        applications = applications.filter(applied_at__date__lte=to_date)

    if sort == 'oldest':
        applications = applications.order_by('applied_at')
    elif sort == 'status':
        applications = applications.order_by('status', '-applied_at')
    elif sort == 'job':
        applications = applications.order_by('job__title', '-applied_at')
    else:
        sort = 'newest'
        applications = applications.order_by('-applied_at')

    filtered_total = applications.count()
    paginator = Paginator(applications, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    query_data = request.GET.copy()
    query_data.pop('page', None)
    filters_query = query_data.urlencode()

    job_options = Job.objects.filter(id__in=base_applications.values_list('job_id', flat=True)).distinct().order_by('title')

    has_active_filters = any([query, status, job_id, from_date_raw, to_date_raw, sort != 'newest'])

    return render(
        request,
        'applications/application_list.html',
        {
            'applications': page_obj,
            'status_form': ApplicationStatusForm(),
            'query': query,
            'status': status,
            'job_id': job_id,
            'from_date': from_date_raw,
            'to_date': to_date_raw,
            'sort': sort,
            'job_options': job_options,
            'status_choices': status_choices,
            'status_totals': status_totals,
            'filtered_total': filtered_total,
            'filters_query': filters_query,
            'has_active_filters': has_active_filters,
        },
    )


@login_required
def update_application_status(request, pk):
    application = get_object_or_404(Application.objects.select_related('job'), pk=pk)
    if request.user != application.job.employer and not has_admin_permission(request.user):
        return HttpResponseForbidden('Bạn không có quyền cập nhật đơn ứng tuyển này.')

    next_url = _get_safe_next_url(request, default='application_list')

    if request.method == 'POST':
        form = ApplicationStatusForm(request.POST, instance=application)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cập nhật trạng thái đơn ứng tuyển thành công.')
        else:
            messages.error(request, 'Trạng thái cập nhật không hợp lệ.')

    return redirect(next_url)
