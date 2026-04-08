from django.urls import path

from .views import ApplyJobView, JobCategoryListView, JobDetailView, JobListCreateView

urlpatterns = [
    path('categories/', JobCategoryListView.as_view(), name='job-category-list'),
    path('', JobListCreateView.as_view(), name='job-list-create'),
    path('<int:pk>/', JobDetailView.as_view(), name='job-detail'),
    path('<int:pk>/apply/', ApplyJobView.as_view(), name='job-apply'),
]
