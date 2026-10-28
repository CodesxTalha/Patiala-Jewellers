from django.urls import path

from . import views

app_name = "shop"

urlpatterns = [
    path("", views.home, name="home"),
    path("collections/", views.collections, name="collections"),
    path("collections/<slug:slug>/", views.product_detail, name="product_detail"),
    path("favorites/", views.favorites, name="favorites"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
]
