"""
Serializers do main_page (API).

Serializer = a "tradutora" entre os modelos Django e o JSON que o app mobile
consome/envia. Cada ModelSerializer le um modelo e expoe os campos escolhidos.

ANINHAMENTO: um Livro tem capitulos; um Capitulo tem cards; um Card tem
subtitulos. Os serializers refletem essa hierarquia para o app receber tudo
pronto numa requisicao so (read), evitando varias idas ao servidor.
"""

from rest_framework import serializers
from main_Page_funcionalidades.models import (
    Livro, Capitulo, Card, Subtitulo, Conexao, AnotacaoCompartilhada, Autor, Obra
)


# ---------- SUBTITULO ----------
class SubtituloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtitulo
        fields = ['id', 'titulo', 'conteudo', 'ordem']


# ---------- CARD ----------
class CardSerializer(serializers.ModelSerializer):
    subtitulos = SubtituloSerializer(many=True, read_only=True)
    imagem_url = serializers.SerializerMethodField()

    class Meta:
        model = Card
        fields = ['id', 'titulo', 'descricao', 'pos_x', 'pos_y', 'imagem_url', 'subtitulos']

    def get_imagem_url(self, obj):
        """Devolve a URL absoluta da imagem (ou None). O app precisa da URL completa."""
        if not obj.imagem:
            return None
        request = self.context.get('request')
        url = obj.imagem.url
        return request.build_absolute_uri(url) if request else url


# ---------- CONEXAO ----------
class ConexaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conexao
        fields = ['id', 'origem', 'destino']


# ---------- CAPITULO ----------
class CapituloSerializer(serializers.ModelSerializer):
    cards = CardSerializer(many=True, read_only=True)
    conexoes = ConexaoSerializer(many=True, read_only=True)

    class Meta:
        model = Capitulo
        fields = ['id', 'numero', 'cards', 'conexoes']


# ---------- LIVRO ----------
class LivroSerializer(serializers.ModelSerializer):
    """
    Serializer de leitura/escrita de Livro. `capa_url` da a URL absoluta da
    capa; `capitulos_com_nota` lista os numeros de capitulos que tem cards
    (mesma regra da biblioteca web).
    """
    capa_url = serializers.SerializerMethodField()
    capitulos_com_nota = serializers.SerializerMethodField()

    class Meta:
        model = Livro
        fields = ['id', 'titulo', 'descricao', 'status', 'capa', 'capa_url',
                  'capitulos_com_nota', 'criado_em']
        read_only_fields = ['id', 'criado_em', 'capa_url', 'capitulos_com_nota']
        extra_kwargs = {'capa': {'write_only': True, 'required': False}}

    def get_capa_url(self, obj):
        if not obj.capa:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(obj.capa.url) if request else obj.capa.url

    def get_capitulos_com_nota(self, obj):
        return list(
            obj.capitulos.filter(cards__isnull=False).distinct()
            .order_by('numero').values_list('numero', flat=True)
        )


# ---------- OBRA / AUTOR (Mural de Casos) ----------
class ObraSerializer(serializers.ModelSerializer):
    capa_url = serializers.SerializerMethodField()

    class Meta:
        model = Obra
        fields = ['id', 'titulo', 'ano', 'capa_url']

    def get_capa_url(self, obj):
        if not obj.capa:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(obj.capa.url) if request else obj.capa.url


class AutorSerializer(serializers.ModelSerializer):
    obras = ObraSerializer(many=True, read_only=True)
    foto_url = serializers.SerializerMethodField()

    class Meta:
        model = Autor
        fields = ['id', 'nome', 'tradicao', 'biografia', 'foto_url', 'obras']

    def get_foto_url(self, obj):
        if not obj.foto:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(obj.foto.url) if request else obj.foto.url


# ---------- ANOTACAO COMPARTILHADA (Arquivo de Evidencias) ----------
class AnotacaoCompartilhadaSerializer(serializers.ModelSerializer):
    autor_nome = serializers.CharField(source='autor.username', read_only=True)
    capa_url = serializers.SerializerMethodField()

    class Meta:
        model = AnotacaoCompartilhada
        fields = ['id', 'titulo_livro', 'autor_nome', 'detalhes', 'qtd_capitulos',
                  'capa_url', 'criado_em']

    def get_capa_url(self, obj):
        if not obj.capa:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(obj.capa.url) if request else obj.capa.url