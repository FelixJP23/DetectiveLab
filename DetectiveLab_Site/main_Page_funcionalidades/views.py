from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required 
from django.views.decorators.http import require_POST
from .models import Livro, Capitulo, Card, Conexao, Subtitulo, AnotacaoCompartilhada, Autor
from django.http import JsonResponse
import json
import pytesseract
from PIL import Image, ImageOps
import shutil, os
from django.conf import settings
from django.core.files.base import ContentFile

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

    livros_com_numero = []
    for i, livro in enumerate(todos):
      
        capitulos_com_nota = (
            livro.capitulos
            .filter(cards__isnull=False)
            .distinct()
            .order_by('numero')
            .values_list('numero', flat=True)
        )
        livros_com_numero.append({
            'numero': i + 1,
            'livro': livro,
            'capitulos': list(capitulos_com_nota),   # ex: [1, 2]
        })

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
        capa=capa,         
    )
    return redirect('biblioteca')

@login_required
@require_POST
def excluir_livro(request, livro_id):
    livro = get_object_or_404(Livro, pk=livro_id, usuario=request.user)
    livro.delete()
    return JsonResponse({'ok': True})
    



@login_required
def quadro(request, livro_id, numero=1):
    livro = get_object_or_404(Livro, pk=livro_id, usuario=request.user)

  
    capitulo, _ = Capitulo.objects.get_or_create(livro=livro, numero=numero)

    capitulos = livro.capitulos.all()
    cards     = capitulo.cards.all()
    conexoes  = capitulo.conexoes.all()

    return render(request, 'quadro.html', {
        'livro': livro,
        'capitulo': capitulo,
        'capitulos': capitulos,
        'cards': cards,
        'conexoes': conexoes,
    })


@login_required
@require_POST
def salvar_quadro(request, capitulo_id):
    capitulo = get_object_or_404(Capitulo, pk=capitulo_id, livro__usuario=request.user)
    dados = json.loads(request.body)

    cards_enviados = dados.get('cards', [])
    id_map = {}
    ids_que_continuam = []

    for c in cards_enviados:
        front_id = str(c.get('id'))
        titulo    = c.get('titulo', '')
        descricao = c.get('descricao', '')
        x = int(c.get('x', 100))
        y = int(c.get('y', 100))
        subtitulos = c.get('subtitulos', [])   

        if front_id.lstrip('-').isdigit() and int(front_id) > 0:
            card = Card.objects.filter(pk=int(front_id), capitulo=capitulo).first()
            if card:
                card.titulo = titulo
                card.descricao = descricao
                card.pos_x = x
                card.pos_y = y
                card.save()
                id_map[front_id] = card
                ids_que_continuam.append(card.id)
        else:
            card = Card.objects.create(
                capitulo=capitulo, titulo=titulo, descricao=descricao, pos_x=x, pos_y=y
            )
            id_map[front_id] = card
            ids_que_continuam.append(card.id)

        
        if front_id in id_map:
            card_obj = id_map[front_id]
            card_obj.subtitulos.all().delete()
            for i, s in enumerate(subtitulos):
                Subtitulo.objects.create(
                    card=card_obj,
                    titulo=s.get('titulo', ''),
                    conteudo=s.get('conteudo', ''),
                    ordem=i,
                )

    capitulo.cards.exclude(id__in=ids_que_continuam).delete()

    capitulo.conexoes.all().delete()
    for con in dados.get('conexoes', []):
        origem  = id_map.get(str(con.get('origem')))
        destino = id_map.get(str(con.get('destino')))
        if origem and destino:
            Conexao.objects.create(capitulo=capitulo, origem=origem, destino=destino)

    return JsonResponse({'ok': True})


@login_required
@require_POST
def novo_capitulo(request, livro_id):
    livro = get_object_or_404(Livro, pk=livro_id, usuario=request.user)
    ultimo = livro.capitulos.order_by('-numero').first()
    proximo = (ultimo.numero + 1) if ultimo else 1
    Capitulo.objects.create(livro=livro, numero=proximo)
    return redirect('quadro', livro_id=livro.id, numero=proximo)


@login_required
@require_POST
def importar_ocr(request, capitulo_id):
    capitulo = get_object_or_404(Capitulo, pk=capitulo_id, livro__usuario=request.user)
    imagem = request.FILES.get('imagem')
    if not imagem:
        return JsonResponse({'ok': False, 'erro': 'Nenhuma imagem enviada'}, status=400)

    try:
        dados_imagem = imagem.read()
        imagem.seek(0)
        from io import BytesIO
        img = Image.open(BytesIO(dados_imagem))
        img = ImageOps.exif_transpose(img)
        proc = ImageOps.autocontrast(ImageOps.grayscale(img))
        texto = pytesseract.image_to_string(proc, lang='por+eng+jpn')
    except Exception as e:
        return JsonResponse({'ok': False, 'erro': str(e)}, status=500)

    linhas = [l.strip() for l in texto.splitlines() if l.strip()]
    if not linhas:
        return JsonResponse({'ok': False, 'erro': 'Nenhum texto reconhecido na imagem'}, status=200)

    card = Card.objects.create(
        capitulo=capitulo, titulo='Diagrama Importado',
        imagem=imagem, pos_x=120, pos_y=120,
    )
    # Um subtitulo por linha reconhecida
    for i, linha in enumerate(linhas):
        Subtitulo.objects.create(card=card, titulo=linha, ordem=i)

    return JsonResponse({
        'ok': True,
        'linhas': linhas,
        'card_id': card.id,
        'imagem_url': card.imagem.url,
    })



def serializar_livro(livro):
    """Congela os capitulos/cards/subtitulos/conexoes de um livro em dict."""
    capitulos_data = []
    for cap in livro.capitulos.all().order_by('numero'):
        cards_data = []
        # mapeia card.id -> indice, para as conexoes referenciarem por indice
        card_index = {}
        for idx, card in enumerate(cap.cards.all().order_by('id')):
            card_index[card.id] = idx
            cards_data.append({
                'titulo': card.titulo,
                'descricao': card.descricao,
                'pos_x': card.pos_x,
                'pos_y': card.pos_y,
                'imagem': card.imagem.name if card.imagem else None,  # caminho relativo em MEDIA
                'subtitulos': [
                    {'titulo': s.titulo, 'conteudo': s.conteudo, 'ordem': s.ordem}
                    for s in card.subtitulos.all().order_by('ordem')
                ],
            })
        conexoes_data = [
            {'origem': card_index.get(c.origem_id), 'destino': card_index.get(c.destino_id)}
            for c in cap.conexoes.all()
            if c.origem_id in card_index and c.destino_id in card_index
        ]
        capitulos_data.append({
            'numero': cap.numero,
            'cards': cards_data,
            'conexoes': conexoes_data,
        })
    return capitulos_data


def aplicar_snapshot(livro, snapshot):
    
    livro.capitulos.all().delete()

    for cap_data in snapshot:
        cap = Capitulo.objects.create(livro=livro, numero=cap_data['numero'])
        cards_criados = []  

        for c in cap_data['cards']:
            novo = Card(
                capitulo=cap,
                titulo=c.get('titulo', ''),
                descricao=c.get('descricao', ''),
                pos_x=c.get('pos_x', 100),
                pos_y=c.get('pos_y', 100),
            )
            
            img_name = c.get('imagem')
            if img_name:
                origem = os.path.join(settings.MEDIA_ROOT, img_name)
                if os.path.exists(origem):
                    with open(origem, 'rb') as f:
                        novo.imagem.save(os.path.basename(img_name), ContentFile(f.read()), save=False)
            novo.save()
            cards_criados.append(novo)

            for s in c.get('subtitulos', []):
                Subtitulo.objects.create(
                    card=novo, titulo=s.get('titulo', ''),
                    conteudo=s.get('conteudo', ''), ordem=s.get('ordem', 0)
                )

       
        for con in cap_data.get('conexoes', []):
            oi, di = con.get('origem'), con.get('destino')
            if oi is not None and di is not None and oi < len(cards_criados) and di < len(cards_criados):
                Conexao.objects.create(
                    capitulo=cap, origem=cards_criados[oi], destino=cards_criados[di]
                )


@login_required
def arquivo_evidencias(request):
    import random
    compartilhadas = list(AnotacaoCompartilhada.objects.all())
    random.shuffle(compartilhadas)  
  
    meus_livros = Livro.objects.filter(usuario=request.user).order_by('id')
    meus_titulos = list(meus_livros.values_list('titulo', flat=True))
    return render(request, 'arquivo_evidencias.html', {
        'compartilhadas': compartilhadas,
        'meus_livros': meus_livros,
        'meus_titulos_json': json.dumps(meus_titulos),
    })


@login_required
@require_POST
def exportar_anotacoes(request):
    livro_id = request.POST.get('livro_id')
    detalhes = request.POST.get('detalhes', '').strip()
    livro = get_object_or_404(Livro, pk=livro_id, usuario=request.user)

    snapshot = serializar_livro(livro)
    AnotacaoCompartilhada.objects.create(
        autor=request.user,
        titulo_livro=livro.titulo,
        capa=livro.capa if livro.capa else None,
        detalhes=detalhes,
        snapshot=snapshot,
        qtd_capitulos=len(snapshot),
    )
    return redirect('arquivo_evidencias')


@login_required
@require_POST
def importar_anotacoes(request, export_id):
    export = get_object_or_404(AnotacaoCompartilhada, pk=export_id)

  
    livro_destino = Livro.objects.filter(
        usuario=request.user, titulo=export.titulo_livro
    ).first()

    if not livro_destino:
        return JsonResponse({
            'ok': False,
            'erro': 'Voce precisa ter "%s" na sua biblioteca para importar.' % export.titulo_livro
        }, status=400)

  
    aplicar_snapshot(livro_destino, export.snapshot)
    return JsonResponse({'ok': True})


@login_required
def mural_casos(request):
    autores = Autor.objects.prefetch_related('obras').all()

 
    autores_json = []
    for a in autores:
        autores_json.append({
            'id': a.id,
            'nome': a.nome,
            'tradicao': a.tradicao,
            'biografia': a.biografia,
            'foto': a.foto.url if a.foto else '',
            'obras': [
                {'titulo': o.titulo, 'ano': o.ano, 'capa': o.capa.url if o.capa else ''}
                for o in a.obras.all()
            ],
        })

    return render(request, 'mural_casos.html', {
        'americanos': [a for a in autores if a.tradicao == 'americana'],
        'japoneses':  [a for a in autores if a.tradicao == 'japonesa'],
        'autores_json': json.dumps(autores_json),
    })
