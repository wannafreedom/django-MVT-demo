from django.conf.urls import url
from django.urls import path
from .views import IndexView, DetailView, ListView

# namespace 和站app_name一起用
app_name = 'goods'
urlpatterns = [
    path('index', IndexView.as_view(), name="index"),
    path('goods/<int:goods_id>', DetailView.as_view(), name="detail"),
    path('list/<int:type_id>/<int:page>', ListView.as_view(), name='list')
]
