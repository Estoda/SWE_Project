from rest_framework import serializers
from . import models
from django.contrib.auth.hashers import make_password


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = "__all__"
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def create(self, validated_data):
        user = models.User(
            username=validated_data["username"],
            email=validated_data["email"],
            password=make_password(validated_data["password"]),
        )
        user.save()
        return user

    def vlidate_username(self, value):
        if models.User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username is already taken")
        return value


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Cart
        fields = "__all__"
