from django.shortcuts import render, redirect, HttpResponse
from .models import User
from django.urls import reverse
from django.views.generic import View
from itsdangerous import TimedJSONWebSignatureSerializer as serial
from itsdangerous import SignatureExpired
from django.conf import settings
from celery_tasks.tasks import sayhello
from django.contrib.auth import authenticate, login, logout
from utils.mixin import LoginRequireMixin
import re
from .models import Address, User
from django_redis import get_redis_connection
from goods.models import GoodsSKU
from order.models import OrderInfo, OrderGoods
from django.core.paginator import Paginator


# Create your views here.
def register(request):
    # 通过请求方式的不同，来确认不同的return
    if request.method == 'get':
        return render(requset, 'register.html')
    else:
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        # all()方法，全为真才为真
        if not all([username, password, email]):
            return render(request, 'register.html', {'errmsg': '数据不完整'})
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None
        if user:
            return render(request, 'register.html', {'errmsg': '用户已存在'})
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()
        print(email)
        return redirect(reverse('goods:index'))


def register_handle(request):
    # 注册处理
    username = request.POST.get('user_name')
    password = request.POST.get('pwd')
    email = request.POST.get('email')
    # all()方法，全为真才为真
    if not all([username, password, email]):
        return render(request, 'register.html', {'errmsg': '数据不完整'})
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = None
    if user:
        return render(request, 'register.html', {'errmsg': '用户已存在'})
    user = User.objects.create_user(username, email, password)
    user.is_active = 0
    user.save()
    print(email)
    return redirect(reverse('goods:index'))


class Register(View):
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        # all()方法，全为真才为真
        if not all([username, password, email]):
            return render(request, 'register.html', {'errmsg': '数据不完整'})
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None
        if user:
            return render(request, 'register.html', {'errmsg': '用户已存在'})
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        serial1 = serial(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        token = serial1.dumps(info)
        token = token.decode()
        # activate
        sayhello.delay('wxw11118888@163.com', username, token)
        return redirect(reverse('goods:index'))


class Activate(View):
    def get(self, request, token):
        serial1 = serial(settings.SECRET_KEY, 3600)
        try:
            info = serial1.loads(token)
            user_id = info["confirm"]
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()
            return redirect(reverse("user:login"))
        except SignatureExpired:
            return HttpResponse("超出时间")


class Login(View):
    def get(self, request):
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = "checked"
        else:
            username = ""
            checked = ""
        return render(request, "login.html", {'username': username, 'checked': checked})

    def post(self, request):
        # 获取数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        # 检验
        if not all([username, password]):
            return render(request, "login.html", {'errmsg': '数据不完整'})

        # 处理，登录处理
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                # 记录登录状态，session
                login(request, user)
                # 登录装饰器，next值的获取
                next_url = request.GET.get('next', reverse('goods:index'))
                response = redirect(next_url)
                # 记住用户名
                remember = request.POST.get("remember")
                if remember == "on":
                    response.set_cookie('username', username, max_age=3600)
                else:
                    response.delete_cookie('username')

                return response
            else:
                return render(request, "login.html", {'errmsg': '未激活状态'})

        else:
            return render(request, "login.html", {'errmsg': '密码错误'})


class UserInfo(LoginRequireMixin, View):
    def get(self, request):
        # django除了给模板文件传递变量，还传递request.user
        page = "user"
        user = request.user
        address = Address.objects.get_default_address(user=user)

        con = get_redis_connection('default')

        history_key = 'history_%d' % user.id

        # 获取用户最新浏览的5个商品的id
        sku_ids = con.lrange(history_key, 0, 4)  # [2,3,1]

        # 从数据库中查询用户浏览的商品的具体信息
        # goods_li = GoodsSKU.objects.filter(id__in=sku_ids)
        #
        # goods_res = []
        # for a_id in sku_ids:
        #     for goods in goods_li:
        #         if a_id == goods.id:
        #             goods_res.append(goods)

        # 遍历获取用户浏览的商品信息
        goods_li = []
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            goods_li.append(goods)

        # 组织上下文
        context = {'page': 'user',
                   'address': address,
                   'goods_li': goods_li}

        # 除了你给模板文件传递的模板变量之外，django框架会把request.user也传给模板文件
        return render(request, 'user_center_info.html', context)


class UserOrder(LoginRequireMixin, View):
    def get(self, request, page):
        '''显示'''
        # 获取用户的订单信息
        user = request.user
        orders = OrderInfo.objects.filter(user=user).order_by('-create_time')

        # 遍历获取订单商品的信息
        for order in orders:
            # 根据order_id查询订单商品信息
            order_skus = OrderGoods.objects.filter(order_id=order.order_id)

            # 遍历order_skus计算商品的小计
            for order_sku in order_skus:
                # 计算小计
                amount = order_sku.count * order_sku.price
                # 动态给order_sku增加属性amount,保存订单商品的小计
                order_sku.amount = amount

            # 动态给order增加属性，保存订单状态标题
            order.status_name = OrderInfo.ORDER_STATUS[order.order_status]
            # 动态给order增加属性，保存订单商品的信息
            order.order_skus = order_skus

        # 分页
        paginator = Paginator(orders, 1)

        # 获取第page页的内容
        try:
            page = int(page)
        except Exception as e:
            page = 1

        if page > paginator.num_pages:
            page = 1

        # 获取第page页的Page实例对象
        order_page = paginator.page(page)

        # todo: 进行页码的控制，页面上最多显示5个页码
        # 1.总页数小于5页，页面上显示所有页码
        # 2.如果当前页是前3页，显示1-5页
        # 3.如果当前页是后3页，显示后5页
        # 4.其他情况，显示当前页的前2页，当前页，当前页的后2页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        # 组织上下文
        context = {'order_page': order_page,
                   'pages': pages,
                   'page': 'order'}

        # 使用模板
        return render(request, 'user_center_order.html', context)


class UserSite(LoginRequireMixin, View):
    def get(self, request):
        user = request.user

        # 获取用户的默认收货地址
        # try:
        #     address = Address.objects.get(user=user, is_default=True) # models.Manager
        # except Address.DoesNotExist:
        #     # 不存在默认收货地址
        #     address = None
        # address = Address.objects.get_default_address(user)
        # address = Address.objects.all(user=user)
        address = Address.objects.filter(user=user)
        # 使用模板
        return render(request, 'user_center_site.html', {'page': 'address', 'address': address})

    def post(self, request):
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')
        if not all([receiver, addr, phone]):
            return render(request, 'user_center_site.html', {'errmsg': '数据不完整'})

            # 校验手机号
        if not re.match(r'^1[3|4|5|7|8][0-9]{9}$', phone):
            return render(request, 'user_center_site.html', {'errmsg': '手机格式不正确'})

            # 业务处理：地址添加
            # 如果用户已存在默认收货地址，添加的地址不作为默认收货地址，否则作为默认收货地址
            # 获取登录用户对应User对象
        user = request.user

        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     # 不存在默认收货地址
        #     address = None

        address = Address.objects.get_default_address(user)

        if address:
            is_default = False
        else:
            is_default = True

            # 添加地址
        Address.objects.create(user=user,
                               receiver=receiver,
                               addr=addr,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_default)

        # 返回应答,刷新地址页面
        return redirect(reverse('user:address'))  # get请求方式


class Logout(View):
    def get(self, request):
        # 推出登录,session数据清除
        logout(request)
        return redirect(reverse("goods:index"))
