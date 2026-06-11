"""
Rotas de autenticacao da API. Prefixadas por /api/auth/ (ver urls.py do projeto).
"""
from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='api_register'),
    path('login/', views.login_api, name='api_login'),
    path('logout/', views.logout_api, name='api_logout'),
    path('me/', views.me, name='api_me'),
]