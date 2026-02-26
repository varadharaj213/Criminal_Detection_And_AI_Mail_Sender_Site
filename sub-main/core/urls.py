from django.urls import path, include
from django.contrib import admin
from .views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', index, name='core'),
    path('dashboard', dashboard, name="dashboard"),
    path('about', about, name="about"),
    path('live', live, name='live'),
    path('stream/', StreamView, name='streamroom'),
    path('getstream', Stream, name='streamdt'),
    path('livestream/', LiveStreamView, name='livestreamroom'),
    path('getlivestream', LiveStream, name='livestreamdt')
]