import pytest
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from model_bakery import baker


@pytest.fixture
def created_user_without_password():
    user = User.objects.create_user(username='user')
    return user


@pytest.fixture
def auth_admin_user():
    user = User.objects.create_user(username='user1', password='password', is_staff=True)
    token, _ = Token.objects.get_or_create(user=user)
    return {'user': user, 'token': token.key}


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def product_info_factory():
    def factory(**kwargs):
        return baker.make('ProductInfo', **kwargs)
    return factory


@pytest.fixture
def orders_factory():
    def factory(**kwargs):
        return baker.make('Order', **kwargs)
    return factory