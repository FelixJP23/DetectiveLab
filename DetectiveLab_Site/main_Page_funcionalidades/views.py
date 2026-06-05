from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Livro

@login_required
def main_page(request):
    todos = list(Livro.objects.filter(usuario=request.user).order_by('id'))

    
    livros_com_numero = [
        (i + 1, livro)
        for i, livro in enumerate(todos)
        if livro.status in ['aberto', 'frio']
    ]

    return render(request, 'main_page.html', {
        'livros_com_numero': livros_com_numero
    })
