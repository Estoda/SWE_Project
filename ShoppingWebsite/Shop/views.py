from django.shortcuts import redirect
from django.shortcuts import render
from django.contrib.auth.hashers import check_password
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from . import serializers
from . import models
import datetime, jwt
from django.conf import settings
from .forms import ProductForm

# Create your views here.


def home(request):
    token = request.COOKIES.get("jwt")
    user = None

    if token:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

        user_id = payload["id"]
        user = models.User.objects.get(id=user_id)

    if user:
        return render(request, "Shop/about.html", {"username": user.username})

    return render(request, "Shop/about.html", {"username": None})


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = serializers.UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return render(request, "Shop/login.html")

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return render(
                request,
                "Shop/login.html",
                {"error_message": "Please enter both username and password"},
            )

        user = models.User.objects.filter(username=username).first()
        if user is None:
            return render(
                request, "Shop/login.html", {"error_message": "User not found!"}
            )

        if not check_password(password, user.password):
            return render(
                request, "Shop/login.html", {"error_message": "Incorrect password!"}
            )

        payload = {
            "id": user.id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
            "iat": datetime.datetime.utcnow(),
        }

        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        response = Response()
        response = redirect("home")
        response.set_cookie(key="jwt", value=token, httponly=True)
        return response


class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        response = Response()
        response.delete_cookie("jwt")
        response.data = {"message": "Logout Done"}
        return response


def product_list(request):
    products = models.Product.objects.all()
    return render(request, "Shop/products.html", {"products": products})


def add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST)  # Form is instantiated with POST data
        if form.is_valid():  # Validate the form
            form.save()  # Save the product
            return redirect("products")  # Redirect to product list after adding
    else:
        form = ProductForm()  # Instantiate the form for GET request (empty form)

    return render(request, "Shop/add_product.html", {"form": form})
