from django.urls import path

from . import admin_center_views
from . import web_views

urlpatterns = [
    path('', web_views.home, name='home'),
    path('accounts/register/', web_views.register_view, name='register'),
    path('accounts/login/', web_views.login_view, name='login'),
    path('accounts/logout/', web_views.logout_view, name='logout'),
    path('accounts/profile/', web_views.account_profile, name='account_profile'),
    path('jobs/create/', web_views.job_create, name='job_create'),
    path('jobs/<int:pk>/', web_views.job_detail, name='job_detail'),
    path('jobs/<int:pk>/edit/', web_views.job_edit, name='job_edit'),
    path('jobs/<int:pk>/delete/', web_views.job_delete, name='job_delete'),
    path('jobs/<int:pk>/apply/', web_views.apply_job, name='job_apply'),
    path('applications/', web_views.applications_view, name='application_list'),
    path(
        'applications/<int:pk>/status/',
        web_views.update_application_status,
        name='application_status_update',
    ),
    path('admin-center/', admin_center_views.admin_center, name='admin_center'),
    path('admin-center/users/', admin_center_views.admin_users, name='admin_users'),
    path('admin-center/jobs/', admin_center_views.admin_jobs, name='admin_jobs'),
    path(
        'admin-center/applications/',
        admin_center_views.admin_applications,
        name='admin_applications',
    ),
    path(
        'admin-center/categories/',
        admin_center_views.admin_categories,
        name='admin_categories',
    ),
    path(
        'admin-center/experience-levels/',
        admin_center_views.admin_exp_levels,
        name='admin_exp_levels',
    ),
    path(
        'admin-center/work-modes/',
        admin_center_views.admin_work_modes,
        name='admin_work_modes',
    ),
    path(
        'admin-center/employment-types/',
        admin_center_views.admin_employment_types,
        name='admin_employment_types',
    ),
]
