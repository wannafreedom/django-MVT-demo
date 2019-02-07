from django.contrib import admin
from .models import OrderInfo


class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'user', 'pay_method']


# Register your models here.
admin.site.register(OrderInfo, OrderAdmin)
