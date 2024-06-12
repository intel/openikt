from django.urls import path
from .views import *

urlpatterns = [
    path('sign-up', RegisterView.as_view(), name='register'),
    path('login', LoginView.as_view(),  name='login'),
    path('logout', logoutView, name='logout')
]
