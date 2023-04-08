import pytest
from django.urls import reverse
from rest_framework.authtoken.admin import User
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.authtoken.models import Token
from ...api.models import Product, Category, Shop, ProductInfo, UserProfile, Order, ConfirmedBasket


@pytest.mark.django_db
def test_registration(api_client):
    url = reverse('registration')
    assert User.objects.all().count() == 0
    data = {
        'first_name': 'Kolya',
        'last_name': 'Kolyanich',
        'email': 'asdasdasd@gmail.com',
        'username': 'justuser',
        'password': 'asdasdasd123456789',
    }
    resp = api_client.post(url, data)
    assert resp.status_code == HTTP_200_OK
    assert User.objects.all().count() == 1


@pytest.mark.django_db
def test_registration_no_arguments(api_client):
    url = reverse('registration')
    data = {}
    resp = api_client.post(url, data)
    assert resp.status_code == HTTP_400_BAD_REQUEST
    assert User.objects.all().count() == 0


@pytest.mark.django_db
def test_login(api_client, created_user_without_password):
    url = reverse('login')
    created_user_without_password.set_password('password')
    created_user_without_password.save()
    data = {
        'username': created_user_without_password.username,
        'password': 'password'
    }
    resp = api_client.post(url, data)
    assert resp.status_code == HTTP_200_OK
    assert resp.data['token'] == Token.objects.get(user=created_user_without_password).key


@pytest.mark.django_db
def test_login_without_password(api_client, created_user_without_password):
    url = reverse('login')
    data = {
        'username': created_user_without_password.username,
    }
    resp = api_client.post(url, data)
    assert resp.status_code == HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_login_without_args(api_client):
    url = reverse('login')
    data = {}
    resp = api_client.post(url, data)
    assert resp.status_code == HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_create_order(api_client, product_info_factory):
    url = reverse('orders')
    product_info = product_info_factory(_quantity=1)
    data = {
        'product': product_info[0].id,
        'quantity': 1
    }
    token, _ = Token.objects.get_or_create(user=User.objects.all().first())
    api_client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    resp = api_client.post(url, data)
    assert resp.status_code == HTTP_200_OK
    assert Order.objects.all().count() == 1


@pytest.mark.django_db
def test_delete_order(api_client, orders_factory):
    url = reverse('orders')
    order = orders_factory(_quantity=1)
    data = {
        'id': order[0].id,
    }
    token, _ = Token.objects.get_or_create(user=order[0].user)
    api_client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    resp = api_client.delete(url, data)
    assert resp.status_code == HTTP_200_OK


@pytest.mark.django_db
def test_get_partner_state(api_client, auth_admin_user):
    url = reverse('partner_order')
    api_client.credentials(HTTP_AUTHORIZATION='Token ' + auth_admin_user['token'])
    resp = api_client.get(url)
    assert resp.status_code == HTTP_200_OK


@pytest.mark.parametrize("state", [True, False])
@pytest.mark.django_db
def test_change_partner_state(api_client, auth_admin_user, state):
    url = reverse('partner_order')
    api_client.credentials(HTTP_AUTHORIZATION='Token ' + auth_admin_user['token'])
    data = {
        'state': state,
    }
    resp = api_client.post(url, data)
    assert resp.status_code == HTTP_200_OK
    assert UserProfile.objects.get(user=auth_admin_user['user']).state == state


@pytest.mark.django_db
def test_get_basket(api_client, orders_factory, auth_admin_user):
    url = reverse('basket')
    orders = orders_factory(_quantity=1,
                            user=auth_admin_user['user'],
                            basket=auth_admin_user['user'].userprofile.basket)
    api_client.credentials(HTTP_AUTHORIZATION='Token ' + auth_admin_user['token'])
    resp = api_client.get(url)
    assert resp.status_code == HTTP_200_OK


@pytest.mark.django_db
def test_confirm_basket(api_client, orders_factory, auth_admin_user):
    url = reverse('basket_confirm')
    orders = orders_factory(_quantity=1,
                            user=auth_admin_user['user'],
                            basket=auth_admin_user['user'].userprofile.basket)
    api_client.credentials(HTTP_AUTHORIZATION='Token ' + auth_admin_user['token'])
    data = {
        'address': 'address',
        'city': 'city',
        'mail': 'новая почта',
        'phone': '+38064554',
        'index': 55235
    }
    resp = api_client.post(url, data)
    assert resp.status_code == HTTP_200_OK
    assert ConfirmedBasket.objects.all().count() == 1


@pytest.mark.django_db
def test_confirm_basket_without_orders(api_client, orders_factory, auth_admin_user):
    url = reverse('basket_confirm')
    api_client.credentials(HTTP_AUTHORIZATION='Token ' + auth_admin_user['token'])
    data = {
        'address': 'address',
        'city': 'city',
        'mail': 'sdfasdasd@gmail.com',
        'phone': '+38064554',
        'index': 55235,
    }
    resp = api_client.post(url, data)
    assert resp.status_code == HTTP_400_BAD_REQUEST
    assert ConfirmedBasket.objects.all().count() == 0




