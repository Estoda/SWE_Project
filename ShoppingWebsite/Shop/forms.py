from django import forms
from .models import User, Product, Card


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "__all__"


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Card
        fields = "__all__"
