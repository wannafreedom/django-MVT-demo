from django.conf.urls import url
from django.urls import path
from .views import register, register_handle
from .views import Register, Login, Activate, UserInfo, UserOrder, UserSite, Logout

# int 匹配0和正整数
# str 匹配任何空字符串但不包括/
# slug 可理解为注释 匹配任何ascii码包括连接线和下划线
# uuid 匹配一个uuid对象（该对象必须包括破折号—，所有字母必须小写）
# path 匹配所有的字符串 包括/（意思就是path前边和后边的所有）
app_name = 'user'
urlpatterns = [
    # path('register', register, name="register"),
    # path('register_handle', register_handle, name="register_handle")
    path('register', Register.as_view(), name="register"),  # 注册
    path('login', Login.as_view(), name="login"),  # 登录
    url(r'^active/(?P<token>.*)$', Activate.as_view(), name="active"),  # django1.1用法
    # path('active/<slug:slug>', Activate.as_view(), name="active"),  # django2.1用法
    path('', UserInfo.as_view(), name="user"),  # 用户信息页
    path('order/<int:page>', UserOrder.as_view(), name="order"),  # 用户订单页
    path('address', UserSite.as_view(), name="address"),  # 用户地址页
    path('logout', Logout.as_view(), name="logout")  # 登出

]
