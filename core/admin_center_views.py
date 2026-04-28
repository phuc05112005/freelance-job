from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from applications.forms import ApplicationStatusForm
from applications.models import Application
from jobs.forms import (
    EmploymentTypeForm,
    ExperienceLevelForm,
    JobCategoryForm,
    WorkModeForm,
)
from jobs.models import EmploymentType, ExperienceLevel, Job, JobCategory, WorkMode
from users.models import User


def _is_admin_user(user):
    return user.is_authenticated and (
        getattr(user, 'role', None) == 'admin' or user.is_staff or user.is_superuser
    )


def admin_required(view_func):
    return user_passes_test(_is_admin_user, login_url='dashboard')(view_func)


@admin_required
def admin_center(request):
    today = timezone.localdate()
    context = {
        'total_users': User.objects.count(),
        'total_jobs': Job.objects.count(),
        'open_jobs': Job.objects.filter(status='open').filter(
            Q(deadline__isnull=True) | Q(deadline__gte=today)
        ).count(),
        'total_applications': Application.objects.count(),
        'pending_applications': Application.objects.filter(status='pending').count(),
        'total_categories': JobCategory.objects.count(),
        'total_exp_levels': ExperienceLevel.objects.count(),
        'total_work_modes': WorkMode.objects.count(),
        'total_employment_types': EmploymentType.objects.count(),
        'latest_jobs': Job.objects.select_related('employer').prefetch_related('categories')[:8],
        'latest_applications': Application.objects.select_related('student', 'job')[:8],
    }
    return render(request, 'admin_center/index.html', context)


@admin_required
def admin_exp_levels(request):
    if request.method == 'POST':
        if request.POST.get('action') == 'delete':
            obj_id = request.POST.get('id')
            obj = get_object_or_404(ExperienceLevel, pk=obj_id)
            obj.delete()
            messages.success(request, 'Đã xóa mức kinh nghiệm.')
            return redirect('admin_exp_levels')

        form = ExperienceLevelForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đã thêm mức kinh nghiệm mới.')
            return redirect('admin_exp_levels')
    else:
        form = ExperienceLevelForm()

    items = ExperienceLevel.objects.annotate(total_jobs=Count('jobs')).order_by('order')
    return render(
        request,
        'admin_center/exp_levels.html',
        {'form': form, 'items': items},
    )


@admin_required
def admin_work_modes(request):
    if request.method == 'POST':
        if request.POST.get('action') == 'delete':
            obj_id = request.POST.get('id')
            obj = get_object_or_404(WorkMode, pk=obj_id)
            obj.delete()
            messages.success(request, 'Đã xóa hình thức làm việc.')
            return redirect('admin_work_modes')

        form = WorkModeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đã thêm hình thức làm việc mới.')
            return redirect('admin_work_modes')
    else:
        form = WorkModeForm()

    items = WorkMode.objects.annotate(total_jobs=Count('jobs')).order_by('name')
    return render(
        request,
        'admin_center/work_modes.html',
        {'form': form, 'items': items},
    )


@admin_required
def admin_employment_types(request):
    if request.method == 'POST':
        if request.POST.get('action') == 'delete':
            obj_id = request.POST.get('id')
            obj = get_object_or_404(EmploymentType, pk=obj_id)
            obj.delete()
            messages.success(request, 'Đã xóa loại việc làm.')
            return redirect('admin_employment_types')

        form = EmploymentTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đã thêm loại việc làm mới.')
            return redirect('admin_employment_types')
    else:
        form = EmploymentTypeForm()

    items = EmploymentType.objects.annotate(total_jobs=Count('jobs')).order_by('name')
    return render(
        request,
        'admin_center/employment_types.html',
        {'form': form, 'items': items},
    )


@admin_required
def admin_users(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        target = get_object_or_404(User, pk=user_id)

        # Thêm đoạn này
        if request.POST.get('action') == 'delete':
            if target == request.user:
                messages.error(request, 'Bạn không thể xóa chính mình.')
                return redirect('admin_users')
            target.delete()
            messages.success(request, f'Đã xóa tài khoản {target.username}.')
            return redirect('admin_users')

        # Phần cũ giữ nguyên
        new_role = request.POST.get('role')
        is_active = request.POST.get('is_active') == 'on'
        if target == request.user and new_role != 'admin':
            messages.error(request, 'Bạn không thể tự hạ quyền tài khoản admin của chính mình.')
            return redirect('admin_users')
        if new_role in {'student', 'employer', 'admin'}:
            target.role = new_role
        target.is_active = is_active
        target.save(update_fields=['role', 'is_active'])
        messages.success(request, 'Cập nhật người dùng thành công.')
        return redirect('admin_users')
    # ... phần GET giữ nguyên

    keyword = request.GET.get('q', '').strip()
    role = request.GET.get('role', '').strip()
    users = User.objects.all().order_by('-date_joined')
    if keyword:
        users = users.filter(
            Q(username__icontains=keyword)
            | Q(email__icontains=keyword)
            | Q(first_name__icontains=keyword)
            | Q(last_name__icontains=keyword)
        )
    if role in {'student', 'employer', 'admin'}:
        users = users.filter(role=role)

    paginator = Paginator(users, 50)
    page_obj = paginator.get_page(request.GET.get('page'))

    query_data = request.GET.copy()
    query_data.pop('page', None)
    filters_query = query_data.urlencode()

    return render(
        request,
        'admin_center/users.html',
        {
            'users': page_obj,
            'keyword': keyword,
            'role': role,
            'filters_query': filters_query,
        },
    )


@admin_required
def admin_jobs(request):
    keyword = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    today = timezone.localdate()
    jobs = Job.objects.select_related('employer').prefetch_related('categories').annotate(
        total_applications=Count('applications')
    )
    if keyword:
        jobs = jobs.filter(Q(title__icontains=keyword) | Q(employer__username__icontains=keyword))
    if status == 'open':
        jobs = jobs.filter(status='open').filter(Q(deadline__isnull=True) | Q(deadline__gte=today))
    elif status == 'expired':
        jobs = jobs.filter(status='open', deadline__lt=today)
    elif status in {'in_progress', 'completed', 'cancelled'}:
        jobs = jobs.filter(status=status)

    paginator = Paginator(jobs.order_by('-created_at'), 50)
    page_obj = paginator.get_page(request.GET.get('page'))

    query_data = request.GET.copy()
    query_data.pop('page', None)
    filters_query = query_data.urlencode()

    return render(
        request,
        'admin_center/jobs.html',
        {
            'jobs': page_obj,
            'keyword': keyword,
            'status': status,
            'filters_query': filters_query,
        },
    )


@admin_required
def admin_applications(request):
    if request.method == 'POST':
        app_id = request.POST.get('application_id')
        application = get_object_or_404(Application, pk=app_id)
        action = request.POST.get('action', 'update_status')
        if action == 'delete':
            application.delete()
            messages.success(request, 'Đã xóa đơn ứng tuyển.')
        else:
            form = ApplicationStatusForm(request.POST, instance=application)
            if form.is_valid():
                form.save()
                messages.success(request, 'Đã cập nhật trạng thái đơn ứng tuyển.')
            else:
                messages.error(request, 'Trạng thái không hợp lệ.')
        return redirect('admin_applications')

    keyword = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    applications = Application.objects.select_related('student', 'job', 'job__employer')
    if keyword:
        applications = applications.filter(
            Q(student__username__icontains=keyword)
            | Q(job__title__icontains=keyword)
            | Q(job__employer__username__icontains=keyword)
            | Q(candidate_email__icontains=keyword)
            | Q(candidate_phone__icontains=keyword)
        )
    if status in {'pending', 'accepted', 'rejected', 'withdrawn'}:
        applications = applications.filter(status=status)

    paginator = Paginator(applications.order_by('-applied_at'), 50)
    page_obj = paginator.get_page(request.GET.get('page'))

    query_data = request.GET.copy()
    query_data.pop('page', None)
    filters_query = query_data.urlencode()

    return render(
        request,
        'admin_center/applications.html',
        {
            'applications': page_obj,
            'keyword': keyword,
            'status': status,
            'filters_query': filters_query,
        },
    )


@admin_required
def admin_categories(request):
    if request.method == 'POST':
        if request.POST.get('action') == 'delete':
            category_id = request.POST.get('category_id')
            category = get_object_or_404(JobCategory, pk=category_id)
            category.delete()
            messages.success(request, 'Đã xóa lĩnh vực.')
            return redirect('admin_categories')

        form = JobCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đã thêm lĩnh vực mới.')
            return redirect('admin_categories')
    else:
        form = JobCategoryForm()

    categories = JobCategory.objects.annotate(total_jobs=Count('jobs')).order_by('name')
    return render(
        request,
        'admin_center/categories.html',
        {'form': form, 'categories': categories},
    )
