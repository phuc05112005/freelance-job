from django.urls import path
from users import views
from .views import LoginView, MeView, RegisterView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('me/', MeView.as_view(), name='me'),
    path('taocv/',views.Tao_CV, name='taocv'),
    path('cv/', views.quanlycv, name='quanlycv'),
    path('suacv/<int:cv_id>/', views.suacv, name='suacv'),
    path('taicv/<int:cv_id>/', views.chitietcv, name='taicv'),
    path('xoacv/<int:cv_id>/', views.xoacv, name='xoacv'),
]
