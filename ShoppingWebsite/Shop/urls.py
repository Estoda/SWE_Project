from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("products/", views.ProductViewSet.as_view({"get": "list"}), name="products"),
    path(
        "products/<int:product_id>/",
        views.ProductItemView.as_view(),
        name="product-item",
    ),
    path(
        "products/add-to-cart/",
        views.ProductViewSet.as_view({"post": "create"}),
        name="product-add-to-cart",
    ),
    path("add_products/", views.AddProductView.as_view(), name="add_product"),
    path("users/", views.UserViewSet.as_view({"get": "list"}), name="users"),
    path("cart/", views.CartViewSet.as_view({"get": "list"}), name="cart_detail"),
    path("cart/cart_item/<int:item_id>", views.CarItemView.as_view(), name="cart-item"),
    path(
        "cart/cart_item/<int:item_id>/update/",
        views.CarItemView.as_view(),
        name="update-cart-item",
    ),
    path(
        "cart/cart_item/<int:item_id>/delete/",
        views.CarItemView.as_view(),
        name="delete-cart-item",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
