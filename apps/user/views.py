from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.urls import reverse
from django.views.generic import View
from django.conf import settings
from django_redis import get_redis_connection
from . import models
from goods.models import GoodsSKU
import re
import itsdangerous
from utils.mixin import LoginRequireMixin


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

        if not all([username, password]):
            return render(request, 'user/login.html', {'errmsg': '数据不完整'})

        user = authenticate(request, username=username, password=password)
        if user is not None:
            # 表示用户已激活
            if user.is_active:
                # 保存secesion
                login(request, user)
                # 获取要调转的页面
                next_url = request.GET.get('next', reverse('goods:index'))
                response = redirect(next_url)
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


class LogoutView(View):
    '''退出登录'''
    def get(self, request):
        logout(request)
        return redirect(reverse('goods:index'))


class UserInfoView(LoginRequireMixin, View):
    '''用户中心信息页'''
    def get(self, request):
        # 获取收获地址
        user = request.user
        address = models.Address.objects.get_default_addr(user=user)
        # 获取最近浏览的商品
        con = get_redis_connection("default")

        history_key = "history_%d"%user.id  # history_id
        # 获取最新浏览的商品sku ID
        sku_id = con.lrange(history_key, 0, 4)
        # 从数据库中查询用户浏览对应的shk商品信息
        goods_li = []
        for id in sku_id:
            goods = GoodsSKU.objects.get(id=id)
            goods_li.append(goods)

        contex = {'page': 'user', 'address': address, 'goods_li': goods_li}
        return render(request, 'user/user_center_info.html', contex)


class UserOrderView(LoginRequireMixin, View):
    '''用户中心订单页'''
    def get(self, request):
        return render(request, 'user/user_center_order.html', {'page': 'order'})


class AddressView(LoginRequireMixin, View):
    '''用户中心地址页'''
    def get(self, request):
        user = request.user
        address = models.Address.objects.get_default_addr(user=user)
        return render(request, 'user/user_center_site.html', {'page': 'address', 'address': address})

    def post(self, request):
        receiver   = request.POST.get('receiver')
        addr       = request.POST.get('addr')
        zip_code   = request.POST.get('zip_code')
        phone      = request.POST.get('phone')
        is_default = request.POST.get('is_default')

        if not all([receiver, addr, phone]):
            return render(request, 'user/user_center_site.html', {'errmsg': '数据不合法'})

        # 业务处理
        user = request.user
        address = models.Address.objects.get_default_addr(user=user)
        if address:
            is_default = False
        else:
            is_default = True

        # 添加地址
        models.Address.objects.create(user=user, receiver=receiver, addr=addr,
                                      zip_code=zip_code, phone=phone, is_default=is_default)
        # 返回应答
        return redirect(reverse('user:address'))
















