"""
Rotas da API do main_page. Todas serao prefixadas por /api/ (ver urls.py do projeto).
Os names tem sufixo _api para nao colidir com as rotas web de mesmo nome.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Livros
    path('livros/', views.livros_list_create, name='api_livros'),
    path('livros/ativos/', views.livros_ativos, name='api_livros_ativos'),
    path('livros/<int:livro_id>/', views.livro_detail, name='api_livro_detail'),

    # Quadro
    path('livros/<int:livro_id>/quadro/', views.quadro_detail, name='api_quadro'),
    path('livros/<int:livro_id>/quadro/<int:numero>/', views.quadro_detail, name='api_quadro_num'),
    path('capitulos/<int:capitulo_id>/salvar/', views.salvar_quadro, name='api_salvar_quadro'),
    path('livros/<int:livro_id>/novo-capitulo/', views.novo_capitulo, name='api_novo_capitulo'),

    # Evidencias
    path('evidencias/', views.evidencias_list, name='api_evidencias'),
    path('evidencias/exportar/', views.exportar_anotacoes, name='api_exportar'),
    path('evidencias/<int:export_id>/importar/', views.importar_anotacoes, name='api_importar'),

    # Mural de casos
    path('mural/', views.mural_casos, name='api_mural'),
]