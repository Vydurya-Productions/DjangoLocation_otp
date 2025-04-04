from django.contrib import admin
from django.urls import path
from . import views  # Import from the geo app

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('mobile',views.mobile,name='mobile'),
    path('otp',views.otp,name='otp'),
]