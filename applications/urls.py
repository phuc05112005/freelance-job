from django.urls import path

from .views import ApplicationStatusUpdateView, MyApplicationListView

urlpatterns = [
    path('my/', MyApplicationListView.as_view(), name='application-my-list'),
    path('<int:pk>/status/', ApplicationStatusUpdateView.as_view(), name='application-status'),
]
