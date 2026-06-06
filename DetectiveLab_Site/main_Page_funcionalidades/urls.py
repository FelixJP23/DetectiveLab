from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_page, name='main_page'),
    path('biblioteca/', views.biblioteca,name='biblioteca'),
    path('livro/<int:livro_id>/editar/', views.editar_livro, name='editar_livro'),
    path('livro/criar/', views.criar_livro, name='criar_livro'),
    path('livro/<int:livro_id>/excluir/', views.excluir_livro, name='excluir_livro'),
    path('evidencias/', views.arquivo_evidencias, name='arquivo_evidencias'),
    path('evidencias/exportar/', views.exportar_anotacoes, name='exportar_anotacoes'),
    path('evidencias/<int:export_id>/importar/', views.importar_anotacoes, name='importar_anotacoes'),

    #A partir daqui é url do QUADRO
    path('livro/<int:livro_id>/quadro/', views.quadro, name='quadro'),
    path('livro/<int:livro_id>/quadro/<int:numero>/', views.quadro, name='quadro'),
    path('capitulo/<int:capitulo_id>/salvar/', views.salvar_quadro, name='salvar_quadro'),
    path('livro/<int:livro_id>/novo-capitulo/', views.novo_capitulo, name='novo_capitulo'),
    path('capitulo/<int:capitulo_id>/ocr/', views.importar_ocr, name='importar_ocr'),
]
