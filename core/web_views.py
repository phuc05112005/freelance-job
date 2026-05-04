from datetime import date

from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Count, Q
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import (
    url_has_allowed_host_and_scheme,
    urlsafe_base64_decode,
    urlsafe_base64_encode,
)

from applications.forms import ApplicationForm, ApplicationStatusForm
from applications.models import Application
from jobs.forms import JobForm
from jobs.models import EmploymentType, FavoriteJob, Job, JobCategory, WorkMode
from users.forms import (
    AccountPasswordChangeForm,
    EmployerRegisterForm,
    ProfileUpdateForm,
    RegisterForm,
)
from users.models import User


def has_admin_permission(user):
    return user.is_authenticated and (
        getattr(user, 'role', None) == 'admin' or user.is_staff or user.is_superuser
    )


def _get_safe_next_url(request, default='home'):
    next_url = request.POST.get('next') or request.GET.get('next')
    if not next_url:
        return default
    if next_url.startswith('/') and not next_url.startswith('//'):
        return next_url
    if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return next_url
    return default


def _parse_date_param(raw_value):
    if not raw_value:
        return None
    try:
        return date.fromisoformat(raw_value)
    except ValueError:
        return None


def _filter_jobs(request):
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

    return jobs.distinct().order_by('-created_at')


def home(request):
    # Check if any filter is active
    is_searching = any(
        request.GET.get(p) for p in ['q', 'status', 'mode', 'category', 'employment', 'salary_type', 'city']
    )

    today = timezone.localdate()
    search_results = None
    if is_searching:
        jobs_qs = _filter_jobs(request)
        paginator = Paginator(jobs_qs, 8)
        search_results = paginator.get_page(request.GET.get('page'))

    # Latest Jobs (Discovery) - Always get latest 8
    latest_jobs = (
        Job.objects.select_related('employer')
        .prefetch_related('categories')
        .filter(status='open')
        .filter(Q(deadline__isnull=True) | Q(deadline__gte=today))
        .order_by('-created_at')[:8]
    )

    stats = {
        'jobs': Job.objects.count(),
        'open_jobs': Job.objects.filter(status='open').filter(
            Q(deadline__isnull=True) | Q(deadline__gte=today)
        ).count(),
        'students': User.objects.filter(role='student').count(),
        'employers': User.objects.filter(role='employer').count(),
    }

    recommended_major_jobs = Job.objects.none()
    nearby_jobs = Job.objects.none()
    if request.user.is_authenticated and request.user.role == 'student':
        major = (request.user.major or '').strip()
        province = (request.user.province or '').strip()
        if major:
            recommended_major_jobs = (
                Job.objects.select_related('employer')
                .prefetch_related('categories')
                .filter(
                    Q(title__icontains=major)
                    | Q(description__icontains=major)
                    | Q(required_skills__icontains=major)
                    | Q(categories__name__icontains=major)
                )
                .distinct()
                .order_by('-created_at')[:8]
            )
        if province:
            nearby_jobs = (
                Job.objects.select_related('employer')
                .prefetch_related('categories')
                .filter(city__icontains=province)
                .distinct()
                .order_by('-created_at')[:8]
            )

    query_data = request.GET.copy()
    query_data.pop('page', None)
    filters_query = query_data.urlencode()

    context = {
        'is_searching': is_searching,
        'search_results': search_results,
        'latest_jobs': latest_jobs,
        'query': request.GET.get('q', ''),
        'status': request.GET.get('status', ''),
        'mode': request.GET.get('mode', ''),
        'category_id': request.GET.get('category', ''),
        'employment': request.GET.get('employment', ''),
        'salary_type': request.GET.get('salary_type', ''),
        'city': request.GET.get('city', ''),
        'categories': JobCategory.objects.all(),
        'stats': stats,
        'work_modes': WorkMode.objects.all(),
        'employment_types': EmploymentType.objects.all(),
        'filters_query': filters_query,
        'recommended_major_jobs': recommended_major_jobs,
        'nearby_jobs': nearby_jobs,
    }
    if request.user.is_authenticated:
        favorite_job_ids = set(
            FavoriteJob.objects.filter(user=request.user).values_list('job_id', flat=True)
        )
    else:
        favorite_job_ids = set()
    context['favorite_job_ids'] = favorite_job_ids
    return render(request, 'home.html', context)


def job_list_all(request):
    jobs_qs = _filter_jobs(request)
    paginator = Paginator(jobs_qs, 8)
    page_obj = paginator.get_page(request.GET.get('page'))

    query_data = request.GET.copy()
    query_data.pop('page', None)
    filters_query = query_data.urlencode()

    context = {
        'page_obj': page_obj,
        'query': request.GET.get('q', ''),
        'status': request.GET.get('status', ''),
        'mode': request.GET.get('mode', ''),
        'category_id': request.GET.get('category', ''),
        'employment': request.GET.get('employment', ''),
        'salary_type': request.GET.get('salary_type', ''),
        'city': request.GET.get('city', ''),
        'categories': JobCategory.objects.all(),
        'work_modes': WorkMode.objects.all(),
        'employment_types': EmploymentType.objects.all(),
        'filters_query': filters_query,
    }
    if request.user.is_authenticated:
        favorite_job_ids = set(
            FavoriteJob.objects.filter(user=request.user).values_list('job_id', flat=True)
        )
    else:
        favorite_job_ids = set()
    context['favorite_job_ids'] = favorite_job_ids
    return render(request, 'jobs/job_list.html', context)


def employer_landing(request):
    return render(request, 'employer/home.html')


def blog(request):
    return render(request, 'pages/blog.html')


def about_us(request):
    return render(request, 'pages/about.html')


def smart_job_tips(request):
    return render(request, 'pages/smart_job_tips.html')


@login_required
def favorite_jobs(request):
    favorites = (
        FavoriteJob.objects.filter(user=request.user)
        .select_related('job', 'job__employer')
        .prefetch_related('job__categories')
    )
    jobs_list = [item.job for item in favorites]
    favorite_job_ids = {job.id for job in jobs_list}
    return render(
        request,
        'jobs/favorite_jobs.html',
        {
            'jobs': jobs_list,
            'favorite_job_ids': favorite_job_ids,
        },
    )


def toggle_favorite_job(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'message': 'Unauthorized'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'message': 'Method not allowed'}, status=405)

    job = get_object_or_404(Job, pk=pk)
    favorite, created = FavoriteJob.objects.get_or_create(user=request.user, job=job)
    if not created:
        favorite.delete()
        is_favorite = False
    else:
        is_favorite = True

    total_favorites = FavoriteJob.objects.filter(user=request.user).count()
    return JsonResponse(
        {
            'ok': True,
            'is_favorite': is_favorite,
            'total_favorites': total_favorites,
        }
    )


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            try:
                user.save()
            except IntegrityError:
                form.add_error('email', 'Email này đã tồn tại. Vui lòng dùng email khác.')
                return render(request, 'auth/register.html', {'form': form})

            current_site = get_current_site(request)
            mail_subject = 'Kích hoạt tài khoản của bạn trên Web Tuyển Dụng'
            message = render_to_string(
                'auth/email_activation.html',
                {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': default_token_generator.make_token(user),
                },
            )
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(mail_subject, message, to=[to_email])
            email.content_subtype = 'html'
            email.send()

            return render(request, 'auth/verify_email_sent.html')
    else:
        form = RegisterForm()

    return render(request, 'auth/register.html', {'form': form})


def employer_register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = EmployerRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.employer_verified = True
            try:
                user.save()
            except IntegrityError:
                form.add_error('email', 'Email này đã tồn tại. Vui lòng dùng email khác.')
                return render(request, 'auth/register_employer.html', {'form': form})

            current_site = get_current_site(request)
            mail_subject = 'Kích hoạt tài khoản nhà tuyển dụng'
            message = render_to_string(
                'auth/email_activation.html',
                {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': default_token_generator.make_token(user),
                },
            )
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(mail_subject, message, to=[to_email])
            email.content_subtype = 'html'
            email.send()

            return render(request, 'auth/verify_email_sent.html')
    else:
        form = EmployerRegisterForm()

    return render(request, 'auth/register_employer.html', {'form': form})


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Tài khoản của bạn đã được xác thực thành công. Vui lòng đăng nhập.')
        return redirect('login')

    messages.error(request, 'Link xác thực không hợp lệ hoặc đã hết hạn!')
    return redirect('home')


def login_view(request):
    if request.user.is_authenticated:
        if has_admin_permission(request.user):
            return redirect('admin_center')
        if request.user.role == 'employer':
            return redirect('employer_home')
        return redirect('home')

    next_url = _get_safe_next_url(request)

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Đăng nhập thành công.')
            if has_admin_permission(user):
                return redirect('admin_center')
            if user.role == 'employer':
                return redirect('employer_home')
            return redirect(next_url)
        messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng.')
    else:
        form = AuthenticationForm(request)

    return render(request, 'auth/login.html', {'form': form, 'next': next_url})


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
    category_id = job.categories.values_list('id', flat=True)
    related_jobs = (
        Job.objects.filter(categories__id__in=category_id)
        .exclude(id=job.id)
        .annotate(same_categories_count=Count('categories'))
        .order_by('-same_categories_count', '-created_at')[:6]
    )
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
        'related_jobs': related_jobs,
    }
    return render(request, 'jobs/job_detail.html', context)


@login_required
def job_create(request):
    if request.user.role != 'employer' and not has_admin_permission(request.user):
        messages.error(request, 'Chỉ tài khoản nhà tuyển dụng mới có thể đăng việc.')
        return redirect('home')

    if request.user.role == 'employer' and not request.user.employer_verified:
        messages.error(
            request,
            'Tài khoản nhà tuyển dụng của bạn chưa được xác thực. Vui lòng liên hệ quản trị viên.',
        )
        return redirect('employer_home')

    if request.method == 'POST':
        form = JobForm(request.POST, request.FILES)
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
        form = JobForm(request.POST, request.FILES, instance=job)
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
        applications = Application.objects.select_related('job', 'job__employer').filter(student=user)
    elif user.role == 'employer':
        applications = Application.objects.select_related('job', 'student').filter(job__employer=user)
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

    job_options = (
        Job.objects.filter(id__in=base_applications.values_list('job_id', flat=True))
        .distinct()
        .order_by('title')
    )

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
            'total_jobs': Job.objects.filter(employer=user).count() if user.role == 'employer' else Job.objects.count(),
        },
    )


@login_required
def employer_jobs(request):
    if request.user.role != 'employer' and not has_admin_permission(request.user):
        messages.error(request, 'Chỉ nhà tuyển dụng mới có thể quản lý danh sách việc làm.')
        return redirect('home')

    keyword = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    today = timezone.localdate()

    jobs_qs = Job.objects.filter(employer=request.user).select_related('employer').prefetch_related('categories').annotate(
        total_applications=Count('applications')
    )

    if keyword:
        jobs_qs = jobs_qs.filter(Q(title__icontains=keyword))

    if status == 'open':
        jobs_qs = jobs_qs.filter(status='open').filter(Q(deadline__isnull=True) | Q(deadline__gte=today))
    elif status == 'expired':
        jobs_qs = jobs_qs.filter(status='open', deadline__lt=today)
    elif status in {'in_progress', 'completed', 'cancelled'}:
        jobs_qs = jobs_qs.filter(status=status)

    paginator = Paginator(jobs_qs.order_by('-created_at'), 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    query_data = request.GET.copy()
    query_data.pop('page', None)
    filters_query = query_data.urlencode()

    return render(
        request,
        'jobs/employer_job_list.html',
        {
            'jobs': page_obj,
            'keyword': keyword,
            'status': status,
            'filters_query': filters_query,
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


@login_required
def application_detail_view(request, pk):
    user = request.user
    application = get_object_or_404(
        Application.objects.select_related('job', 'student', 'job__employer'), 
        pk=pk
    )
    
    # Kiểm tra quyền xem: Phải là chủ tin tuyển dụng, sinh viên nộp đơn, hoặc admin
    if user != application.student and user != application.job.employer and not has_admin_permission(user):
        return HttpResponseForbidden('Bạn không có quyền xem chi tiết đơn ứng tuyển này.')
        
    return render(request, 'applications/application_detail.html', {
        'app': application,
        'status_form': ApplicationStatusForm(instance=application) if user == application.job.employer or has_admin_permission(user) else None,
        'status_choices': (
            ('pending', 'Chờ duyệt'),
            ('accepted', 'Đã chấp nhận'),
            ('rejected', 'Đã từ chối'),
        )
    })


def GoiY(request, id):
    job = get_object_or_404(Job, id=id)
    category_id = job.categories.values_list('id', flat=True)
    related_jobs = (
        Job.objects.filter(categories__id__in=category_id)
        .exclude(id=job.id)
        .annotate(same_categories_count=Count('categories'))
        .order_by('-same_categories_count', '-created_at')[:6]
    )
    context = {'job': job, 'related_jobs': related_jobs}
    return render(request, 'jobs')
