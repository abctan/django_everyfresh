from django.urls import path
from . import views

app_name = 'user'

urlpatterns = [
    path('register', views.RegisterView.as_view(), name='register'),       # 注册页
    path('active/<str:token>', views.ActiveView.as_view(), name='active'), # 激活注册链接
    path('login', views.LoginView.as_view(), name='login'),                # 登录页
    path('logout', views.LogoutView.as_view(), name='logout'),             # 注销登录
    path('', views.UserInfoView.as_view(), name='user'),                   # 用户中心也
    path('order', views.UserOrderView.as_view(), name='order'),            # 用户订单页
    path('address', views.AddressView.as_view(), name='address'),          # 用户地址页
]