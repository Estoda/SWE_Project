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
    path("add_products/", views.AddProductView.as_view(), name="add_product"),
    path("users/", views.UserViewSet.as_view({"get": "list"}), name="users"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
