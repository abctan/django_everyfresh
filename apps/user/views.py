from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import authenticate, login
from django.core.mail import send_mail
from django.urls import reverse
from django.views.generic import View
from . import models
from django.conf import settings
import re
import itsdangerous


# Create your views here.
class RegisterView(View):
    def get(self, request):
        return render(request, 'user/register.html')

    def post(self, request):
        # 获取用户数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 校验数据
        if not all([username, password, email]):
            return render(request, 'user/register.html', {'errmsg': '数据不完整'})
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'user/register.html', {'errmsg': '邮箱格式不正确'})
        if allow != 'on':
            return render(request, 'user/register.html', {'errmsg': '请同意协议'})

        # 判断输入用户名是否已注册
        try:
            user = models.User.objects.get(username=username)
        except models.User.DoesNotExist:
            user = None  # 该用户不存在
        if user:
            return render(request, 'user/register.html', {'errmsg': '用户名已存在'})

        # 数据入库
        user = models.User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        # 生成激活链接
        serializer = itsdangerous.TimedJSONWebSignatureSerializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info)
        # 发邮箱
        subject = '天天生鲜欢迎您'
        message = ''
        html_message = "<h1>%s,欢迎您成为天天生鲜注册会员</h1>请点击下方链接激活您的账户<br/><a href='http://127.0.0.1:8000/user/active/%s'>http://127.0.0.1:8000/user/active/%s</a>"\
                  %(user.username, token.decode('utf-8'), token.decode('utf-8'))
        sender = settings.EMAIL_FROM
        receiver = [email]
        send_mail(subject, message, sender, receiver, html_message=html_message)

        return redirect(reverse('goods:index'))


class ActiveView(View):
    '''用户激活类视图'''
    def get(self, request, token):
        serializer = itsdangerous.TimedJSONWebSignatureSerializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token.encode('utf-8'))
            user_id = info['confirm']

            user = models.User.objects.get(id=user_id)
            user.is_active = 1
            user.save()
            # 跳转到登录页面
            return redirect(reverse('user:login'))
        except itsdangerous.SignatureExpired:
            # 激活链接已过期
            return HttpResponse('激活链接已过期')
        except itsdangerous.BadData:
            return HttpResponse('链接不合法')



class LoginView(View):
    '''登录页面'''
    def get(self, request):
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked  = 'checked'
        else:
            username = ''
            checked  = ''

        return render(request, 'user/login.html', {'username': username, 'checked': checked})

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        rember   = request.POST.get('rember')

        print(rember)
        if not all([username, password]):
            return render(request, 'user/login.html', {'errmsg': '数据不完整'})

        user = authenticate(request, username=username, password=password)
        if user is not None:
            # 表示用户已激活
            if user.is_active:
                # 保存secesion
                login(request, user)
                response = redirect(reverse('goods:index'))
                # 保存用户名操作
                if rember == 'on':
                    response.set_cookie('username', username, max_age=7*24*3600)
                else:
                    response.delete_cookie('username')
                # 返回response
                return response
            else:
                return render(request, 'user/login.html', {'errmsg': '账户未激活'})
        else:
            # Return an 'invalid login' error message.
            return render(request, 'user/login.html', {'errmsg': '用户名或者密码错误'})