from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario_customizado



admin.site.register(Usuario_customizado,UserAdmin)


