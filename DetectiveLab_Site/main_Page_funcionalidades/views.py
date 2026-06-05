from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required 
from django.views.decorators.http import require_POST
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


@login_required
def biblioteca(request):
    todos = list(Livro.objects.filter(usuario=request.user).order_by('id'))

    livros_com_numero = [
        (i + 1, livro)
        for i, livro in enumerate(todos)
    ]

    return render(request, 'biblioteca.html', {
        'livros_com_numero': livros_com_numero
    })


@login_required
@require_POST
def editar_livro(request, livro_id):
    
    livro = get_object_or_404(Livro, pk=livro_id, usuario=request.user)

    status = request.POST.get('status')
    descricao = request.POST.get('descricao', '').strip()

    if status in ['aberto', 'frio', 'concluido']:
        livro.status = status
    livro.descricao = descricao
    livro.save()

    return redirect('biblioteca')

@login_required
@require_POST
def criar_livro(request):
    titulo    = request.POST.get('titulo', '').strip()
    descricao = request.POST.get('descricao', '').strip()
    status    = request.POST.get('status', 'aberto')
    capa      = request.FILES.get('capa')

    
    if not titulo:
        return redirect('biblioteca')

    if status not in ['aberto', 'frio', 'concluido']:
        status = 'aberto'

    Livro.objects.create(
        usuario=request.user,
        titulo=titulo,
        descricao=descricao,
        status=status,
        capa=capa,             # pode ser None se nao foi enviada
    )

    return redirect('biblioteca')