from django.contrib.auth.models import User
from django.db import models

# Create your models here.
from django.db.models.signals import post_save
from django_rest_passwordreset.tokens import get_token_generator


class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name='userprofile', on_delete=models.CASCADE)
    logo = models.ImageField(upload_to='logo/')
    # basket

    def __str__(self):
        return self.user.username


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        Basket.objects.create(user=instance.userprofile)


post_save.connect(create_user_profile, sender=User)


class Category(models.Model):
    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    name = models.CharField(max_length=50, unique=True)


class Product(models.Model):
    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField()
    model = models.CharField(null=True, max_length=128)
    price = models.PositiveIntegerField()
    image = models.ImageField()
    # parameters
    # orders


class Parameter(models.Model):
    class Meta:
        verbose_name = 'Parameter'
        verbose_name_plural = 'Parameters'

    name = models.CharField(max_length=150)
    products = models.ManyToManyField('Product', related_name='parameters', through='ProductParameter')


class ProductParameter(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    parameter = models.ForeignKey('Parameter', on_delete=models.CASCADE)
    value = models.CharField(max_length=100)


class Order(models.Model):
    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dt = models.DateField(auto_now_add=True)
    product = models.ForeignKey('Product', related_name='orders', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    basket = models.ForeignKey('Basket', on_delete=models.CASCADE, related_name='orders', null=True, blank=True)
    confirmed_basket = models.ForeignKey('ConfirmedBasket', on_delete=models.CASCADE, related_name='orders', null=True,
                                         blank=True)


class Basket(models.Model):
    class Meta:
        verbose_name = 'Basket'
        verbose_name_plural = 'Baskets'

    user = models.OneToOneField('UserProfile', related_name='basket', on_delete=models.CASCADE)
    # orders


class ConfirmedBasket(models.Model):
    class Meta:
        verbose_name = 'Confirmed order'
        verbose_name_plural = 'Confirmed orders'

    MAILS = [
        ('нова почта', 'Нова почта'),
        ('укр почта', 'Укр почта'),
    ]

    # orders
    address = models.CharField(max_length=128)
    phone = models.CharField(max_length=20)
    city = models.CharField(max_length=128)
    mail = models.CharField(max_length=30, choices=MAILS, default='нова почта')
    index = models.PositiveIntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='confirmed_basket')


class Contact(models.Model):
    class Meta:
        verbose_name = 'Contact'
        verbose_name_plural = 'Contacts'

    phone = models.CharField(unique=True, null=True, blank=True, max_length=20)
    address = models.CharField(null=True, blank=True, max_length=128)
    city = models.CharField(max_length=128, null=True, blank=True)
    index = models.PositiveIntegerField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class ConfirmEmailToken(models.Model):
    user = models.ForeignKey(User, related_name='confirm_email_tokens', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    key = models.CharField(max_length=64, unique=True, db_index=True)

    @staticmethod
    def generate_key():
        return get_token_generator().generate_token()

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super(ConfirmEmailToken, self).save(*args, **kwargs)
