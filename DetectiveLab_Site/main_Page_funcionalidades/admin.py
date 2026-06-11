from django.contrib import admin
from .models import Livro, Autor, Obra

@admin.register(Livro)
class LivroAdmin(admin.ModelAdmin):
    list_display  = ('titulo', 'usuario', 'status', 'criado_em')
    list_filter   = ('status',)
    search_fields = ('titulo', 'usuario__username')

class ObraInline(admin.TabularInline):
    model = Obra
    extra = 1

@admin.register(Autor)
class AutorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tradicao', 'ordem')
    list_filter = ('tradicao',)
    inlines = [ObraInline]

