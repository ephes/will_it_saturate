# export django.urls
from django.urls import path

from will_it_saturate.django import views

urlpatterns = [
    path("<str:base>/<str:path>/<int:num>", views.serve_file),
]
