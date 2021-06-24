# AUTOGENERATED! DO NOT EDIT! File to edit: 15_django_urls.ipynb (unless otherwise specified).

__all__ = ['urlpatterns']

# Cell
from django.urls import path

from . import views

urlpatterns = [
    path("serve_sync_filesystem/<str:base>/<str:path>/<int:num>", views.serve_sync_filesystem),
    path("serve_async_filesystem/<str:base>/<str:path>/<int:num>", views.serve_async_filesystem),
    path("server_sync_minio/<str:base>/<str:path>/<int:num>", views.serve_sync_minio),
    path("serve_async_minio/<str:base>/<str:path>/<int:num>", views.serve_async_minio),
    path("serve_async_django_fileresponse/<str:base>/<str:path>/<int:num>", views.serve_async_django_fileresponse),
        path("serve_async_django_fileresponse_minio/<str:base>/<str:path>/<int:num>", views.serve_async_django_fileresponse_minio),
]