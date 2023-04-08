from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Order, Product, Basket, UserProfile, ConfirmedBasket, ConfirmEmailToken


class ProductListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = ('id', 'name', 'category')


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('model', 'quantity', 'price', 'price_rrc')


class OrderSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField()

    class Meta:
        model = Order
        fields = ('id', 'product', 'dt', 'quantity')

    def to_representation(self, instance):
        self.fields['product'] = ProductSerializer(read_only=True)
        return super(OrderSerializer, self).to_representation(instance)


# class OrderPartnerSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Order
#         fields = ('id', 'status', 'product', 'dt')
#
#     def to_representation(self, instance):
#         self.fields['product'] = ProductInfoSerializer(read_only=True)
#         return super(OrderPartnerSerializer, self).to_representation(instance)


# class PartnerStateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = UserProfile
#         fields = ('state',)

#
# class BasketSerializer(serializers.ModelSerializer):
#     orders = OrderSerializer(many=True, read_only=True)
#
#     class Meta:
#         model = Basket
#         fields = ('orders',)


class ConfirmedBasketSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfirmedBasket
        fields = ('address', 'phone', 'city', 'mail', 'index')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'username', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


# class PartnerSerializer(serializers.ModelSerializer):
#     product = ProductInfoSerializer(read_only=True)
#     user = UserSerializer(read_only=True)
#
#     class Meta:
#         model = Order
#         fields = ['id', 'product', 'status', 'dt', 'quantity', 'user']


class ConfirmEmailTokenSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = ConfirmEmailToken
        fields = ['user']

