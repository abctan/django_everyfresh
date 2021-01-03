from django.urls import path
from . import views

app_name = 'user'

urlpatterns = [
    path('register', views.RegisterView.as_view(), name='register'),
    path('active/<str:token>', views.ActiveView.as_view(), name='active'), # 激活注册链接
    path('login', views.LoginView.as_view(), name='login')
]