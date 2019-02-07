from django.conf.urls import url
from .views import CartAddView, CartInfoView, CartDeleteView, CartUpdateView
from django.urls import path

app_name = 'cart'
urlpatterns = [
    path('add', CartAddView.as_view(), name='add'),
    path('', CartInfoView.as_view(), name='show'),
    path('update', CartUpdateView.as_view(), name='update'),
    path('delete', CartDeleteView.as_view(), name='delete')
]
