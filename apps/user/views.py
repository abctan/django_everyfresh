from django.shortcuts import render, redirect
from django.urls import reverse
from . import models
import re


# Create your views here.
def register(request):
    if request.POST:
        # 获取用户数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 校验数据
        if not all([username, password, email]):
            return render(request, 'user/register.html', {'errmsg':'数据不完整'})
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'user/register.html', {'errmsg': '邮箱格式不正确'})
        if allow != 'on':
            return render(request, 'user/register.html', {'errmsg': '请同意协议'})

        # 判断输入用户名是否已注册
        try:
            user = models.User.objects.get(username=username)
        except models.User.DoesNotExist:
            user = None # 该用户不存在
        if user:
            return render(request, 'user/register.html', {'errmsg': '用户名已存在'})

        # 数据入库
        user = models.User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()
        return redirect(reverse('goods:index'))

    return render(request, 'user/register.html')
