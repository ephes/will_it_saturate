# AUTOGENERATED! DO NOT EDIT! File to edit: 15_django_urls.ipynb (unless otherwise specified).

__all__ = ['urlpatterns_sync_filesystem', 'urlpatterns_async_filesystem', 'urlpatterns_sync_minio',
           'urlpatterns_async_minio', 'urlpatterns']

# Cell
from django.urls import path

from . import views

urlpatterns_sync_filesystem = [
    path("<str:base>/<str:path>/<int:num>", views.serve_sync_filesystem),
]

urlpatterns_async_filesystem = [
    path("<str:base>/<str:path>/<int:num>", views.serve_async_filesystem),
]

urlpatterns_sync_minio = [
    path("<str:base>/<str:path>/<int:num>", views.serve_sync_minio),
]

urlpatterns_async_minio = [
    path("<str:base>/<str:path>/<int:num>", views.serve_async_minio),
]

urlpatterns = urlpatterns_sync_filesystem