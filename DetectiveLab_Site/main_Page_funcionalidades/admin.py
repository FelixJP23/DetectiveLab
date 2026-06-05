from django.contrib import admin
from .models import Livro

@admin.register(Livro)
class LivroAdmin(admin.ModelAdmin):
    list_display  = ('titulo', 'usuario', 'status', 'criado_em')
    list_filter   = ('status',)
    search_fields = ('titulo', 'usuario__username')
