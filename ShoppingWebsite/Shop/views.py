from django.shortcuts import redirect
from django.shortcuts import render
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import check_password
from rest_framework import permissions, status, viewsets
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
        return render(
            request,
            "Shop/about.html",
            {"username": user.username, "is_superuser": user.is_superuser},
        )

    return render(request, "Shop/about.html", {"username": None})


class UserViewSet(viewsets.ModelViewSet):
    queryset = models.User.objects.all()
    serializer_class = serializers.UserSerializer
    permission_classes = [permissions.AllowAny]

    def list(self, request):
        token = request.COOKIES.get("jwt")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload["id"]
        user = models.User.objects.get(id=user_id)
        users = models.User.objects.all()
        return render(
            request,
            "Shop/users.html",
            {
                "users": users,
                "username": user.username,
                "is_superuser": user.is_superuser,
            },
        )


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return render(request, "Shop/register.html")

    def post(self, request):
        serializer = serializers.UserSerializer(data=request.data)
        if not serializer.is_valid():
            # Pass errors to the template
            return render(
                request,
                "Shop/register.html",
                {"error_messages": serializer.errors},
            )
        user = serializer.save()

        payload = {
            "id": user.id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
            "iat": datetime.datetime.utcnow(),
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        response = redirect("home")
        response.set_cookie(key="jwt", value=token, httponly=True)
        return response


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
        # superuser = authenticate(request, username=username, password=password)
        # if superuser:
        #     user = superuser
        #     login(request, user)
        #     return redirect("home")

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

    def get(self, request):
        response = redirect("home")
        response.delete_cookie("jwt")
        response.delete_cookie("csrftoken")
        response.delete_cookie("sessionid")
        return response

    # def post(self, request):
    #     response = redirect("home")  # Redirect to the home page
    #     response.delete_cookie("jwt")  # Delete the JWT cookie
    #     return response


class ProductViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    def list(self, request):
        products = models.Product.objects.all()
        token = request.COOKIES.get("jwt")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload["id"]
        user = models.User.objects.get(id=user_id)
        return render(
            request,
            "Shop/products.html",
            {
                "products": products,
                "username": user.username,
                "is_superuser": user.is_superuser,
            },
        )


def product_list(request):
    token = request.COOKIES.get("jwt")
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    user_id = payload["id"]
    user = models.User.objects.get(id=user_id)
    products = models.Product.objects.all()
    return render(
        request,
        "Shop/products.html",
        {
            "products": products,
            "username": user.username,
            "is_superuser": user.is_superuser,
        },
    )


class AddProductView(APIView):
    permission_classes = [permissions.AllowAny]

    def dispatch(self, request, *args, **kwargs):
        token = request.COOKIES.get("jwt")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload["id"]
        user = models.User.objects.get(id=user_id)
        if not user.is_superuser:
            return render(
                request,
                "Shop/add_product.html",
                {
                    "error_message": "You do not have access to this page (Admin Only)!",
                    "username": user.username,
                    "is_superuser": user.is_superuser,
                },
            )
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        form = ProductForm()
        token = request.COOKIES.get("jwt")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload["id"]
        user = models.User.objects.get(id=user_id)
        return render(
            request,
            "Shop/add_product.html",
            {
                "form": form,
                "username": user.username,
                "is_superuser": user.is_superuser,
            },
        )

    def post(self, request):
        form = ProductForm(request.POST, request.FILES)
        name = request.data.get("name")
        price = request.data.get("price")
        stock = request.data.get("stock")

        if not name or not price or not stock:
            render(
                request,
                "Shop/add_product.html",
                {"error_message": "Please fill in all fields!"},
            )

        if form.is_valid():
            form.save()
            return redirect("products")  # Redirect to the product list or home page
        return render(
            request,
            "Shop/add_product.html",
            {"form": form, "error_message": "Invalid data. Please try again."},
        )
