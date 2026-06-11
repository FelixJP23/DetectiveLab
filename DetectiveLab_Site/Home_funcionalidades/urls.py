from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .forms import EmailLoginForm
urlpatterns =  [

    path('', views.home, name='home'),
    path("Register/", views.register, name="Register"),
    path('login/', auth_views.LoginView.as_view( template_name='login.html', authentication_form=EmailLoginForm ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name = 'logout'),

]