from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_page, name='main_page'),
    path('biblioteca/', views.biblioteca,name='biblioteca'),
    path('livro/<int:livro_id>/editar/', views.editar_livro, name='editar_livro'),
    path('livro/criar/', views.criar_livro, name='criar_livro'),
]
