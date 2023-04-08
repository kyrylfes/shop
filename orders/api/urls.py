from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path, include
from rest_framework import routers
from rest_framework.authtoken.views import obtain_auth_token
from django.contrib.auth import views as auth_views

from .views import ProductListView, OrderView, BasketView, RegistrationView, \
  ConfirmEmailView, ConfirmedOrdersView, UserLoginView, ProfileView, delete_order, edit_order, edit_product, \
  delete_product, DiagramsView, add_product

router = routers.SimpleRouter()
router.register(r'products', ProductListView, basename='products')
# router.register(r'partner/order', PartnerView, basename='partner_order')

urlpatterns = [
  # path('update/', ImportView.as_view(), name='import'),
  path('', include(router.urls)),
  path('profile/', ProfileView.as_view(), name='profile'),
  path('signup/', RegistrationView.as_view(), name='signup'),
  path('change_password/', auth_views.PasswordChangeView.as_view(), name='change_password'),
  path('login/', UserLoginView.as_view(), name='login'),
  path('logout/', LogoutView.as_view(next_page=settings.LOGOUT_REDIRECT_URL), name='logout'),
  path('basket/', BasketView.as_view(), name='basket'),
  # path('basket/confirm/', ConfirmOrderView.as_view(), name='basket_confirm'),
  path('confirmed/', ConfirmedOrdersView.as_view(), name='confirmed_orders'),
  path('orders/', OrderView.as_view(), name='orders'),
  path('del_order/', delete_order, name='delete_order'),
  path('add_product/', add_product, name='add_product'),
  path('edit_order/', edit_order, name='edit_order'),
  path('edit_product/<int:pk>/', edit_product, name='edit_product'),
  path('del_product/<int:pk>/', delete_product, name='delete_product'),
  # path('partner/state/', PartnerStateView.as_view(), name='partner_order'),
  path('registration/confirm/', ConfirmEmailView.as_view(), name='registration_confirm'),
  path('diagrams/', DiagramsView.as_view(), name='diagrams'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL,
                                                                         document_root=settings.STATIC_ROOT)

handler404 = "api.views.page_not_found_view"
