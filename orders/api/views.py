import asyncio
from webbrowser import get

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail, EmailMultiAlternatives
from django.core.validators import URLValidator
from django.db.models import Max, Min, Count
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .tasks import send_email

import plotly.express as px
import pandas as pd

# Create your views here.
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views.generic import CreateView
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ViewSet
from yaml import load, Loader

from .models import Category, Product, Parameter, ProductParameter, Order, Basket, UserProfile, \
    ConfirmedBasket, ConfirmEmailToken, Contact
from .serializers import ProductListSerializer, ProductSerializer, UserSerializer, \
    ConfirmedBasketSerializer, ConfirmEmailTokenSerializer, OrderSerializer


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = User.objects.get(id=request.user.id)
        confirmed_baskets = ConfirmedBasket.objects.filter(user=request.user)
        data = {
            'user': user,
            'confirmed_baskets': confirmed_baskets
        }

        return render(request, 'profile.html', data)


class UserLoginView(APIView):
    def get(self, request, *args, **kwargs):
        return render(request, 'login.html')

    def post(self, request, *args, **kwargs):
        try:
            user = User.objects.get(username=request.data.get('username'))
            login(request, user)
            return redirect('products-list')
        except User.DoesNotExist:
            return render(request, 'login.html', {'errors': 'Incorrect data provided'})


class RegistrationView(APIView):
    def get(self, request, *args, **kwargs):
        return render(request, 'signup.html')

    def post(self, request, *args, **kwargs):
        '''
        Registration view, required fields: first_name, last_name, password, email, username
        with confirm email
        '''
        try:
            password = request.data.get('password')
            validate_password(password)
        except Exception as password_er:
            return render(request, 'signup.html', {'password_er': password_er})
        else:
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                is_user_registered = User.objects.filter(email=serializer.validated_data.get('email')).first()
                if not is_user_registered:
                    user = serializer.save()
                    user.is_active = False
                    user.is_staff = False
                    user.set_password(request.data.get('password'))
                    user.save()
                    token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user.id)
                    # send_email.delay(token.key, token.user.email)

                    msg = EmailMultiAlternatives(
                        f"Password Reset Token for {token.user.email}",
                        'something',
                        settings.EMAIL_HOST_USER,
                        [token.user.email]
                    )
                    msg.attach_alternative(
                        render_to_string('email.html', {'token': token.key, 'email': token.user.email}), "text/html")
                    msg.send()

                    return redirect('products-list')
                return render(request, 'signup.html', {'email_er': 'Email already exist'})
            return render(request, 'signup.html', {'serializer_er': serializer.errors})


class ConfirmEmailView(APIView):
    def get(self, request, *args, **kwargs):
        token = request.GET.get('token')
        email = request.GET.get('email')
        token = ConfirmEmailToken.objects.filter(user__email=email,
                                                 key=token).first()
        if token:
            token.user.is_active = True
            token.user.save()
            token.delete()

            return redirect('products-list')
        return render(request, 'confirm_email.html', {'errors': 'This token is expired'})


class DiagramsView(APIView):
    def get(self, request):
        # Count the number of products in each category
        products_per_category = Product.objects.values('category__name').annotate(count=Count('id'))

        # Convert the result to a pandas DataFrame
        df_categories = pd.DataFrame(products_per_category)

        # Generate an interactive pie chart of the product categories
        fig_categories = px.pie(df_categories, values='count', names='category__name')

        # Count the number of products with different quantities
        quantity_counts = Product.objects.annotate(num_orders=Count('orders')).values('name', 'num_orders')

        # Convert the result to a pandas DataFrame
        df_quantities = pd.DataFrame(quantity_counts)

        # Generate an interactive bar chart of the product quantities
        fig_quantities = px.bar(df_quantities, x='name', y='num_orders')

        # Render the HTML template with the charts
        return render(request, 'diagrams.html', {
            'product_categories': fig_categories.to_html(full_html=False),
            'product_quantities': fig_quantities.to_html(full_html=False),
        })


class ProductListView(ViewSet):
    def create(self, request, *args, **kwargs):
        if request.user == AnonymousUser:
            return
        serializer = OrderSerializer(data=request.data)

        if serializer.is_valid():
            order = Order.objects.create(user=request.user,
                                         product=serializer.validated_data.get('product'),
                                         quantity=serializer.validated_data.get('quantity'),
                                         basket=request.user.userprofile.basket, )
        return redirect('basket')

    def list(self, request, *args, **kwargs):
        search = self.request.GET.get('search')
        ordering = '-price'
        if self.request.GET.get('ordering'):
            ordering = self.request.GET.get('ordering')
        minprice = self.request.GET.get('minprice')
        maxprice = self.request.GET.get('maxprice')
        category = self.request.GET.get('category')

        if category:
            products = Product.objects.filter(category=Category.objects.get(id=category), price__gte=minprice,
                                              price__lte=maxprice).order_by(ordering)
        elif search:
            products = Product.objects.filter(name__contains=search, price__gte=minprice, price__lte=maxprice).order_by(
                ordering)
        elif minprice and maxprice:
            products = Product.objects.filter(price__gte=minprice, price__lte=maxprice).order_by(ordering)
        else:
            products = Product.objects.all().order_by(ordering)

        categories = Category.objects.all()
        maxprice = Product.objects.aggregate(Max('price'))
        minprice = Product.objects.aggregate(Min('price'))

        data = {
            'products_list': products,
            'categories': categories,
            'max_price': maxprice['price__max'],
            'min_price': minprice['price__min']
        }

        return render(request, 'products.html', data)

    def retrieve(self, request, pk=None):
        '''
        Info about specific product by pk
        '''
        product = Product.objects.get(id=pk)

        data = {
            'product': product
        }

        return render(request, 'single_product.html', data)


class OrderView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        '''
        Delete order from basket and in general
        '''
        order = Order.objects.get(id=request.data.get('id'))
        if order.user == request.user:
            order.delete()
            return JsonResponse({'Status': True}, status=HTTP_200_OK)
        return JsonResponse({'Status': False, 'Errors': 'Can delete only yourself order'}, status=HTTP_400_BAD_REQUEST)


def delete_order(request):
    order = Order.objects.get(id=request.POST.get('order'))
    order.delete()
    return redirect('basket')


def edit_order(request):
    order = Order.objects.get(id=request.POST.get('order'))
    order.quantity = request.POST.get('quantity')
    order.save()
    return redirect('basket')


def delete_product(request, pk):
    if request.user.is_staff:
        order = Product.objects.get(id=pk)
        order.delete()
        return redirect('products-list')


def add_product(request):
    categories = Category.objects.all()
    if request.method == 'POST' and request.user.is_staff:
        product, is_created = Product.objects.get_or_create(name=request.POST.get('name'),
                                                            quantity=request.POST.get('quantity'),
                                                            model=request.POST.get('model'),
                                                            category=Category.objects.get(
                                                                id=request.POST.get('category')),
                                                            price=request.POST.get('price'),
                                                            image=request.FILES["image"])
        if is_created:
            return redirect('products-list')
    return render(request, 'add_product.html', {'categories': categories})


def edit_product(request, pk):
    categories = Category.objects.all()
    if request.method == 'POST' and request.user.is_staff:
        image = request.FILES["image"]
        product = Product.objects.get(id=pk)
        product.quantity = request.POST.get('quantity')
        product.name = request.POST.get('name')
        product.model = request.POST.get('model')
        product.price = request.POST.get('price')
        product.category = Category.objects.get(name=request.POST.get('category'))
        product.image = image

        product.save()
        return redirect('products-list')
    return render(request, 'edit_product.html', {'categories': categories})


class BasketView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        basket = Basket.objects.get(user=request.user.userprofile)
        data = {
            'basket': basket,
        }
        return render(request, 'basket.html', data)

    def post(self, request, *args, **kwargs):
        serializer = ConfirmedBasketSerializer(data=request.data)
        data = {
            'basket': request.user.userprofile.basket
        }

        if serializer.is_valid():
            orders = Order.objects.filter(basket=request.user.userprofile.basket)
            for order in orders:
                if order.product.quantity <= order.quantity:
                    data[
                        'quantity_er'] = f'Unfortunately we have a limited amount of product "{order.product.name}", please choose a different amount.'
                    return render(request, 'basket.html', data)
            confirmed_basket = ConfirmedBasket.objects.create(address=serializer.validated_data.get('address'),
                                                              city=serializer.validated_data.get('city'),
                                                              index=serializer.validated_data.get('index'),
                                                              mail=serializer.validated_data.get('mail'),
                                                              phone=serializer.validated_data.get('phone'),
                                                              user=request.user)
            for order in orders:
                order.confirmed_basket = confirmed_basket
                order.basket = None
                order.save()

            return redirect('profile')
        data['field_er'] = serializer.errors.get('index')[0]
        return render(request, 'basket.html', data)


class ConfirmedOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        queryset = ConfirmedBasket.objects.filter(user=request.user)
        serializer = ConfirmedBasketSerializer(queryset, many=True)
        return Response(serializer.data)


# class PartnerView(ViewSet):
#     permission_classes = [IsAdminUser]
#
#     def list(self, request, *args, **kwargs):
#         '''
#         List of partner orders
#         '''
#         queryset = Order.objects.filter(product__shop__user=self.request.user)
#         serializer = OrderPartnerSerializer(queryset, many=True)
#         return Response(serializer.data)
#
#     def retrieve(self, request, pk=None):
#         '''
#         Get specific partner order by id
#         '''
#         queryset = Order.objects.get(id=pk)
#         serializer = OrderPartnerSerializer(queryset)
#         return Response(serializer.data)


# class PartnerStateView(APIView):
#     permission_classes = [IsAdminUser]
#
#     def get(self, request, *args, **kwargs):
#         '''
#         Get partner state
#         '''
#         queryset = UserProfile.objects.get(user=request.user)
#         return JsonResponse({'state': queryset.state})
#
#     def post(self, request, *args, **kwargs):
#         '''
#         Change partner state
#         Required field: 'state' with value - on or off
#         '''
#         if {'state'}.issubset(request.data):
#             serializer = PartnerStateSerializer(data=request.data)
#
#             if serializer.is_valid():
#                 userprofile = UserProfile.objects.get(user=request.user)
#                 userprofile.state = serializer.validated_data.get('state')
#                 userprofile.save()
#                 return JsonResponse({'Status': True})
#             return JsonResponse({'Status': False, 'Errors': serializer.errors}, status=HTTP_400_BAD_REQUEST)
#         return JsonResponse({'Status': False, 'Errors': 'All required arguments not provided'},
#                             status=HTTP_400_BAD_REQUEST)

# class ImportView(APIView):
#     permission_classes = [IsAdminUser]
#
#     def post(self, request, *args, **kwargs):
#         '''
#         Import yaml file with info about shop, categories and products
#         '''
#         file = request.data.get('file')
#
#         if file:
#             data = load(file, Loader=Loader)
#
#             shop, _ = Shop.objects.get_or_create(name=data['shop'], user=self.request.user)
#
#             for category in data['categories']:
#                 category_obj, _ = Category.objects.get_or_create(name=category['name'], id=category['id'])
#
#             for product in data['goods']:
#                 product_obj, _ = Product.objects.get_or_create(name=product['name'],
#                                                                category=Category.objects.get(id=product['category']))
#                 product_info_obj, _ = ProductInfo.objects.get_or_create(product=product_obj,
#                                                                         shop=shop,
#                                                                         quantity=product['quantity'],
#                                                                         id=product['id'],
#                                                                         model=product['model'],
#                                                                         price=product['price'],
#                                                                         price_rrc=product['price_rrc'])
#
#                 for parameter, value in product['parameters'].items():
#                     parameter_obj, _ = Parameter.objects.get_or_create(name=parameter)
#                     product_parameter_obj, _ = ProductParameter.objects.get_or_create(product_info=product_info_obj,
#                                                                                       parameter=parameter_obj,
#                                                                                       value=value)
#
#             return JsonResponse({'Status': True})
#         return JsonResponse({'Status': False, 'Error': 'No file'}, status=HTTP_400_BAD_REQUEST)
#
#     def put(self, request, *args, **kwargs):
#         '''
#         Change products info via yaml file
#         '''
#         file = request.data.get('file')
#
#         if file:
#             data = load(file, Loader=Loader)
#             shop, _ = Shop.objects.get_or_create(name=data['shop'], user=self.request.user)
#
#             for category in data['categories']:
#                 category_obj, _ = Category.objects.get_or_create(name=category['name'], id=category['id'])
#
#             for product in data['goods']:
#                 product_obj, _ = Product.objects.get_or_create(name=product['name'],
#                                                                category=product['category'])
#                 product_info_obj, _ = ProductInfo.objects.get_or_create(product=product_obj,
#                                                                         shop=shop,
#                                                                         id=product['id'], )
#                 product_info_obj.update(price=product['price'],
#                                         price_rcc=product['price_rrc'],
#                                         quantity=product['quantity'])
#
#                 for parameter, value in product['parameters'].items():
#                     parameter_obj, _ = Parameter.objects.get_or_create(name=parameter)
#                     product_parameter_obj, _ = ProductParameter.objects.get_or_create(product_info=product_info_obj,
#                                                                                       parameter=parameter_obj,
#                                                                                       value=value)
#
#             return JsonResponse({'Status': True})
#         return JsonResponse({'Status': False, 'Error': 'No file'}, status=HTTP_400_BAD_REQUEST)
#
#     def delete(self, request, *args, **kwargs):
#         '''
#         Delete products from db via yaml file
#         '''
#         file = request.data.get('file')
#
#         if file:
#             data = load(file, Loader=Loader)
#             shop, _ = Shop.objects.get(name=data['shop'], user=self.request.user)
#
#             for product in data['goods']:
#                 product_obj = Product.objects.get(name=product['name'],
#                                                   category=product['category'])
#                 product_info_obj = ProductInfo.objects.get(product=product_obj,
#                                                            shop=shop,
#                                                            id=product['id'], )
#
#                 for parameter, value in product['parameters'].items():
#                     parameter_obj, _ = Parameter.objects.get(products__product_info=product_info_obj).delete()
#                     product_parameter_obj, _ = ProductParameter.objects.get(product_info=product_info_obj).delete()
#
#                 product_info_obj.delete()
#
#             return JsonResponse({'Status': True})
#         return JsonResponse({'Status': False, 'Error': 'No file'}, status=HTTP_400_BAD_REQUEST)


def page_not_found_view(request, exception):
    return render(request, '404.html', status=404)
