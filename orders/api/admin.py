from django.contrib import admin

# Register your models here.

from .models import Product, Order, Category, Basket, Parameter, ProductParameter, ConfirmEmailToken, \
    Contact, ConfirmedBasket, UserProfile

admin.site.register(Product)
admin.site.register(Order)
admin.site.register(Category)
admin.site.register(Basket)
admin.site.register(ConfirmedBasket)
admin.site.register(ConfirmEmailToken)
admin.site.register(UserProfile)