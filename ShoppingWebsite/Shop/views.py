from django.shortcuts import redirect, render, get_object_or_404
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
from django.db.models import Q

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
    queryset = models.Product.objects.all()

    def list(self, request):
        products = models.Product.objects.all()
        token = request.COOKIES.get("jwt")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload["id"]
        user = models.User.objects.get(id=user_id)

        search_query = request.GET.get("search", "")
        if search_query:
            products = models.Product.objects.filter(Q(name__icontains=search_query))

        return render(
            request,
            "Shop/products.html",
            {
                "products": products,
                "username": user.username,
                "is_superuser": user.is_superuser,
            },
        )

    def create(self, request):
        token = request.COOKIES.get("jwt")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload["id"]
        user = models.User.objects.get(id=user_id)
        if not user:
            return render(
                request,
                "Shop/products.html",
                {"error_message": "Please, login or register first!"},
            )

        quantity = int(request.data.get("quantity", 1))
        product_id = request.data.get("product_id")

        if not product_id:
            return render(
                request,
                "Shop/products.html",
                {"error_message": "Product ID is required!"},
            )

        product = models.Product.objects.filter(id=product_id).first()

        if not product:
            return render(
                request, "Shop/products.html", {"error_message": "Product not found!"}
            )

        if quantity > product.stock:
            return render(
                request,
                "Shop/products.html",
                {"error_message": "Not enough stock available!"},
            )

        product.stock -= quantity
        product.save()

        cart, _ = models.Cart.objects.get_or_create(user=user)
        cart_item, created = models.CartItem.objects.get_or_create(
            cart=cart, product=product
        )
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity

        cart_item.total = cart_item.product.price * cart_item.quantity
        cart_item.save()

        return redirect("cart_detail")


class ProductItemView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.ProductSerializer

    def get(self, request, product_id=None):
        token = request.COOKIES.get("jwt")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload["id"]
        user = models.User.objects.get(id=user_id)
        if not user:
            return redirect("login")

        product = models.Product.objects.filter(id=product_id).first()
        serializer = self.serializer_class(product)
        if not product:
            return render(
                request,
                "Shop/product_item.html",
                {
                    "error_message": "Product not found!",
                    "product": product,
                    "username": user.username,
                    "is_superuser": user.is_superuser,
                },
            )
        return render(
            request,
            "Shop/product_item.html",
            {
                "error_message": None,
                "product": product,
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
            return redirect("products")
        return render(
            request,
            "Shop/add_product.html",
            {"form": form, "error_message": "Invalid data. Please try again."},
        )


class CartViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    def list(self, request):
        products = models.Product.objects.all()
        token = request.COOKIES.get("jwt")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload["id"]
        user = models.User.objects.get(id=user_id)
        if not user:
            return redirect("login")

        cart, _ = models.Cart.objects.get_or_create(user=user)
        context = {
            "cart": cart,
            "items": cart.items.all(),
            "total": cart.get_total(),
            "username": user.username,
            "is_superuser": user.is_superuser,
        }
        return render(request, "Shop/cart_detail.html", context)


class CarItemView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.CartItemSerializer

    def get(self, request, item_id=None):
        token = request.COOKIES.get("jwt")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload["id"]
        user = models.User.objects.get(id=user_id)
        if not user:
            return redirect("login")

        cart, _ = models.Cart.objects.get_or_create(user=user)
        item = get_object_or_404(cart.items, id=item_id)
        serializer = self.serializer_class(item)
        if not item:
            return render(
                request,
                "Shop/cart_item.html",
                {
                    "error_message": "Item not found!",
                    "item": item,
                    "total": cart.get_total(),
                    "username": user.username,
                    "is_superuser": user.is_superuser,
                },
            )
        return render(
            request,
            "Shop/cart_item.html",
            {
                "error_message": None,
                "item": item,
                "total": cart.get_total(),
                "username": user.username,
                "is_superuser": user.is_superuser,
            },
        )

    def put(self, request, item_id):
        token = request.COOKIES.get("jwt")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload["id"]
        user = models.User.objects.get(id=user_id)
        if not user:
            return redirect("login")

        data = request.data.copy()
        cart, _ = models.Cart.objects.get_or_create(user=user)
        item = get_object_or_404(cart.items, id=item_id)
        data["cart"] = cart.id  # Include the cart ID
        data["product"] = item.product.id  # Include the product ID
        serializer = self.serializer_class(item, data=data)
        if serializer.is_valid():
            updated_item = serializer.save()
            updated_item.total = updated_item.product.price * updated_item.quantity
            updated_item.save()

            cart.total = cart.get_total()
            cart.save()
            return render(
                request,
                "Shop/cart_item.html",
                {
                    "error_message": None,
                    "item": item,
                    "total": cart.get_total(),
                    "username": user.username,
                    "is_superuser": user.is_superuser,
                },
            )
        else:
            return render(
                request,
                "Shop/cart_item.html",
                {
                    "error_message": serializer.errors,
                    "item": item,
                    "total": cart.get_total(),
                    "username": user.username,
                    "is_superuser": user.is_superuser,
                },
            )

    def post(self, request, item_id=None):
        if request.POST.get("_method") == "PUT":
            return self.put(request, item_id)
        elif request.POST.get("_method") == "DELETE":
            return self.delete(request, item_id)
        return Response(
            {"detail": "Method not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def delete(self, request, item_id=None):
        token = request.COOKIES.get("jwt")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload["id"]
        user = models.User.objects.get(id=user_id)
        if not user:
            return redirect("login")

        cart, _ = models.Cart.objects.get_or_create(user=user)
        item = get_object_or_404(cart.items, id=item_id)

        if item:
            product = item.product
            product.stock += item.quantity
            product.save()
            item.delete()
            return render(
                request,
                "Shop/cart_detail.html",
                {
                    "error_message": None,
                    "items": cart.items.all(),
                    "total": cart.get_total(),
                    "username": user.username,
                    "is_superuser": user.is_superuser,
                },
            )
