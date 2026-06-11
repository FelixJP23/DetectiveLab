"""
Views da API do main_page.

Todas exigem usuario autenticado (IsAuthenticated, ja e o default no settings,
mas deixamos explicito por clareza). A logica espelha exatamente as views web:
mesmos filtros por usuario, mesma numeracao estavel de casos, mesma regra de
import (titulo igual + substituir), e reaproveita serializar_livro /
aplicar_snapshot que ja existem em main_Page_funcionalidades.views.

Por que function-based views com @api_view: mantem a logica explicita e proxima
da versao web (mais facil de comparar), em vez de esconder em ViewSets.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from main_Page_funcionalidades.models import (
    Livro, Capitulo, Card, Subtitulo, Conexao, AnotacaoCompartilhada, Autor
)
# Reaproveita a logica de snapshot ja existente na aplicacao web
from main_Page_funcionalidades.views import serializar_livro, aplicar_snapshot

from .serializers import (
    LivroSerializer, CapituloSerializer, AutorSerializer,
    AnotacaoCompartilhadaSerializer
)


# =====================================================================
#  LIVROS
# =====================================================================
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def livros_list_create(request):
    """
    GET  -> lista os livros do usuario logado (todos, como na biblioteca).
    POST -> cria um livro novo (titulo obrigatorio).
    """
    if request.method == 'GET':
        livros = Livro.objects.filter(usuario=request.user).order_by('id')
        ser = LivroSerializer(livros, many=True, context={'request': request})
        return Response(ser.data)

    # POST
    titulo = (request.data.get('titulo') or '').strip()
    if not titulo:
        return Response({'erro': 'O titulo e obrigatorio.'}, status=status.HTTP_400_BAD_REQUEST)

    status_livro = request.data.get('status', 'aberto')
    if status_livro not in ['aberto', 'frio', 'concluido']:
        status_livro = 'aberto'

    livro = Livro.objects.create(
        usuario=request.user,
        titulo=titulo,
        descricao=(request.data.get('descricao') or '').strip(),
        status=status_livro,
        capa=request.FILES.get('capa'),
    )
    ser = LivroSerializer(livro, context={'request': request})
    return Response(ser.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def livros_ativos(request):
    """
    Dossies ativos (main_page): apenas 'aberto'/'frio', com numeracao ESTAVEL
    (baseada na ordem de criacao, igual a web).
    """
    todos = list(Livro.objects.filter(usuario=request.user).order_by('id'))
    ativos = []
    for i, livro in enumerate(todos):
        if livro.status in ['aberto', 'frio']:
            data = LivroSerializer(livro, context={'request': request}).data
            data['numero'] = i + 1   # numero estavel
            ativos.append(data)
    return Response(ativos)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def livro_detail(request, livro_id):
    """
    GET    -> detalhe de um livro.
    PUT    -> edita status e/ou descricao (como editar_livro).
    DELETE -> exclui o livro (cascata leva capitulos/cards/etc).
    Sempre filtrado por usuario=request.user (seguranca: 404 se for de outro).
    """
    livro = get_object_or_404(Livro, pk=livro_id, usuario=request.user)

    if request.method == 'GET':
        ser = LivroSerializer(livro, context={'request': request})
        return Response(ser.data)

    if request.method == 'PUT':
        novo_status = request.data.get('status')
        if novo_status in ['aberto', 'frio', 'concluido']:
            livro.status = novo_status
        if 'descricao' in request.data:
            livro.descricao = (request.data.get('descricao') or '').strip()
        livro.save()
        ser = LivroSerializer(livro, context={'request': request})
        return Response(ser.data)

    # DELETE
    livro.delete()
    return Response({'ok': True}, status=status.HTTP_200_OK)


# =====================================================================
#  QUADRO (capitulos / cards / conexoes / subtitulos)
# =====================================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def quadro_detail(request, livro_id, numero=1):
    """
    Abre um capitulo do quadro. Garante o capitulo 1 (get_or_create), igual a
    web. Retorna o capitulo atual (com cards/conexoes), a lista de capitulos
    do livro e o id do livro.
    """
    livro = get_object_or_404(Livro, pk=livro_id, usuario=request.user)
    capitulo, _ = Capitulo.objects.get_or_create(livro=livro, numero=numero)

    cap_ser = CapituloSerializer(capitulo, context={'request': request})
    capitulos = list(livro.capitulos.order_by('numero').values('id', 'numero'))
    return Response({
        'livro_id': livro.id,
        'livro_titulo': livro.titulo,
        'capitulo_atual': cap_ser.data,
        'capitulos': capitulos,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def salvar_quadro(request, capitulo_id):
    """
    Salva o estado do quadro (mesma logica da web): atualiza cards existentes
    (id>0), cria novos (id temporario negativo), remove os que sumiram, regrava
    subtitulos e recria conexoes. O corpo JSON tem o mesmo formato do front web:
      { "cards": [ {id, titulo, descricao, x, y, subtitulos:[{titulo,conteudo}]} ],
        "conexoes": [ {origem, destino} ] }
    """
    capitulo = get_object_or_404(Capitulo, pk=capitulo_id, livro__usuario=request.user)
    dados = request.data

    cards_enviados = dados.get('cards', [])
    id_map = {}
    ids_que_continuam = []

    for c in cards_enviados:
        front_id = str(c.get('id'))
        titulo = c.get('titulo', '')
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
                    card=card_obj, titulo=s.get('titulo', ''),
                    conteudo=s.get('conteudo', ''), ordem=i
                )

    capitulo.cards.exclude(id__in=ids_que_continuam).delete()

    capitulo.conexoes.all().delete()
    for con in dados.get('conexoes', []):
        origem = id_map.get(str(con.get('origem')))
        destino = id_map.get(str(con.get('destino')))
        if origem and destino:
            Conexao.objects.create(capitulo=capitulo, origem=origem, destino=destino)

    return Response({'ok': True})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def novo_capitulo(request, livro_id):
    """Cria o proximo capitulo sequencial e o retorna."""
    livro = get_object_or_404(Livro, pk=livro_id, usuario=request.user)
    ultimo = livro.capitulos.order_by('-numero').first()
    proximo = (ultimo.numero + 1) if ultimo else 1
    cap = Capitulo.objects.create(livro=livro, numero=proximo)
    return Response({'id': cap.id, 'numero': cap.numero}, status=status.HTTP_201_CREATED)


# =====================================================================
#  ARQUIVO DE EVIDENCIAS (exportar / importar)
# =====================================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def evidencias_list(request):
    """
    Lista as anotacoes compartilhadas (todas), mais os titulos dos livros do
    usuario — o app usa isso para aplicar a regra de import (so titulo igual).
    """
    compartilhadas = AnotacaoCompartilhada.objects.all()
    ser = AnotacaoCompartilhadaSerializer(compartilhadas, many=True, context={'request': request})
    meus_titulos = list(
        Livro.objects.filter(usuario=request.user).values_list('titulo', flat=True)
    )
    return Response({'compartilhadas': ser.data, 'meus_titulos': meus_titulos})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def exportar_anotacoes(request):
    """Exporta um livro do usuario como AnotacaoCompartilhada (congela snapshot)."""
    livro_id = request.data.get('livro_id')
    detalhes = (request.data.get('detalhes') or '').strip()
    livro = get_object_or_404(Livro, pk=livro_id, usuario=request.user)

    snapshot = serializar_livro(livro)
    export = AnotacaoCompartilhada.objects.create(
        autor=request.user,
        titulo_livro=livro.titulo,
        capa=livro.capa if livro.capa else None,
        detalhes=detalhes,
        snapshot=snapshot,
        qtd_capitulos=len(snapshot),
    )
    ser = AnotacaoCompartilhadaSerializer(export, context={'request': request})
    return Response(ser.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def importar_anotacoes(request, export_id):
    """
    Importa anotacoes para um livro do usuario com TITULO IGUAL.
    SUBSTITUI as anotacoes atuais (regra definida). Sem livro de mesmo titulo,
    retorna 400.
    """
    export = get_object_or_404(AnotacaoCompartilhada, pk=export_id)
    livro_destino = Livro.objects.filter(
        usuario=request.user, titulo=export.titulo_livro
    ).first()

    if not livro_destino:
        return Response(
            {'ok': False, 'erro': 'Voce precisa ter "%s" na sua biblioteca para importar.' % export.titulo_livro},
            status=status.HTTP_400_BAD_REQUEST
        )

    aplicar_snapshot(livro_destino, export.snapshot)
    return Response({'ok': True})


# =====================================================================
#  MURAL DE CASOS (autores / obras)
# =====================================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mural_casos(request):
    """Lista os autores (com obras) separados por tradicao."""
    autores = Autor.objects.prefetch_related('obras').all()
    ser = AutorSerializer(autores, many=True, context={'request': request})
    return Response({
        'americanos': [a for a in ser.data if a['tradicao'] == 'americana'],
        'japoneses':  [a for a in ser.data if a['tradicao'] == 'japonesa'],
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def importar_ocr(request, capitulo_id):

    capitulo = get_object_or_404(Capitulo, pk=capitulo_id, livro__usuario=request.user)
    imagem = request.FILES.get('imagem')
    if not imagem:
        return Response({'ok': False, 'erro': 'Nenhuma imagem enviada'}, status=status.HTTP_400_BAD_REQUEST)

    import pytesseract
    from PIL import Image, ImageOps
    from io import BytesIO

    try:
        dados_imagem = imagem.read()
        imagem.seek(0)
        img = Image.open(BytesIO(dados_imagem))
        img = ImageOps.exif_transpose(img)
        proc = ImageOps.autocontrast(ImageOps.grayscale(img))
        texto = pytesseract.image_to_string(proc, lang='por+eng+jpn')
    except Exception as e:
        return Response({'ok': False, 'erro': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    linhas = [l.strip() for l in texto.splitlines() if l.strip()]
    if not linhas:
        return Response({'ok': False, 'erro': 'Nenhum texto reconhecido na imagem'}, status=status.HTTP_200_OK)

    card = Card.objects.create(
        capitulo=capitulo, titulo='Diagrama Importado', imagem=imagem, pos_x=120, pos_y=120,
    )
    for i, linha in enumerate(linhas):
        Subtitulo.objects.create(card=card, titulo=linha, ordem=i)

    url = card.imagem.url
    return Response({
        'ok': True,
        'linhas': linhas,
        'card_id': card.id,
        'imagem_url': request.build_absolute_uri(url),
    })