"""
Testes unitarios do app main_Page_funcionalidades.

Cobre: modelos (Livro, Capitulo, Card, Subtitulo, Conexao, AnotacaoCompartilhada),
as views de biblioteca/quadro/capitulos, a exclusao de livro, e a feature de
exportar/importar anotacoes (Arquivo de Evidencias).

COMO ESTES TESTES FUNCIONAM
---------------------------
- `TestCase` cria um banco isolado e descarta tudo ao fim de cada teste.
- `setUp` cria um usuario e ja o autentica (force_login) para os testes que
  exigem login (@login_required). force_login pula a tela de senha — e o jeito
  padrao de "fingir" um usuario logado em teste.
- Criamos um SEGUNDO usuario em alguns testes para garantir ISOLAMENTO: um
  usuario nunca pode ver/editar/excluir os livros de outro.
- Para POSTs que enviam JSON (salvar quadro, importar), usamos
  content_type='application/json' e json.dumps, imitando o fetch do front.
- A view de OCR (Tesseract) NAO e testada aqui, conforme combinado: depende de
  binario do sistema e nao e deterministica.

Para rodar:  python manage.py test main_Page_funcionalidades
"""

import json
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import (
    Livro, Capitulo, Card, Subtitulo, Conexao, AnotacaoCompartilhada
)

User = get_user_model()


# =====================================================================
#  MODELOS
# =====================================================================
class ModelosTest(TestCase):
    """Verifica criacao, relacionamentos e exclusao em cascata."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='dono', email='dono@noir.com', password='x'
        )

    def test_cria_livro_com_status_padrao(self):
        """Um livro recem-criado guarda titulo, dono e status corretamente."""
        livro = Livro.objects.create(usuario=self.user, titulo='Caso Um', status='aberto')
        self.assertEqual(livro.titulo, 'Caso Um')
        self.assertEqual(livro.usuario, self.user)
        self.assertEqual(livro.status, 'aberto')

    def test_hierarquia_livro_capitulo_card_subtitulo(self):
        """
        Verifica a cadeia de relacionamentos:
        Livro -> Capitulo -> Card -> Subtitulo, usando os related_name.
        """
        livro = Livro.objects.create(usuario=self.user, titulo='Caso', status='aberto')
        cap = Capitulo.objects.create(livro=livro, numero=1)
        card = Card.objects.create(capitulo=cap, titulo='Pista', descricao='...')
        sub = Subtitulo.objects.create(card=card, titulo='Linha 1', conteudo='nota', ordem=0)

        # Navegacao pelos related_name (livro.capitulos, capitulo.cards, card.subtitulos)
        self.assertEqual(livro.capitulos.count(), 1)
        self.assertEqual(cap.cards.count(), 1)
        self.assertEqual(card.subtitulos.first(), sub)

    def test_exclusao_em_cascata(self):
        """
        Apagar o livro deve apagar capitulos, cards, subtitulos e conexoes juntos
        (on_delete=CASCADE). Se alguem trocar para SET_NULL/PROTECT, isto quebra.
        """
        livro = Livro.objects.create(usuario=self.user, titulo='Caso', status='aberto')
        cap = Capitulo.objects.create(livro=livro, numero=1)
        c1 = Card.objects.create(capitulo=cap, titulo='A')
        c2 = Card.objects.create(capitulo=cap, titulo='B')
        Subtitulo.objects.create(card=c1, titulo='s', conteudo='c', ordem=0)
        Conexao.objects.create(capitulo=cap, origem=c1, destino=c2)

        livro.delete()

        # Tudo que pendurava no livro deve ter sumido
        self.assertEqual(Capitulo.objects.count(), 0)
        self.assertEqual(Card.objects.count(), 0)
        self.assertEqual(Subtitulo.objects.count(), 0)
        self.assertEqual(Conexao.objects.count(), 0)

    def test_conexao_nao_duplicada(self):
        """
        O unique_together(origem, destino) impede duas conexoes identicas.
        Tentar criar a segunda deve levantar erro de integridade.
        """
        from django.db import IntegrityError, transaction
        livro = Livro.objects.create(usuario=self.user, titulo='C', status='aberto')
        cap = Capitulo.objects.create(livro=livro, numero=1)
        a = Card.objects.create(capitulo=cap, titulo='A')
        b = Card.objects.create(capitulo=cap, titulo='B')
        Conexao.objects.create(capitulo=cap, origem=a, destino=b)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Conexao.objects.create(capitulo=cap, origem=a, destino=b)


# =====================================================================
#  BIBLIOTECA / MAIN PAGE
# =====================================================================
class BibliotecaViewTest(TestCase):
    """Testa as listagens (biblioteca e main_page) e a numeracao de casos."""

    def setUp(self):
        self.user = User.objects.create_user(username='u', email='u@u.com', password='x')
        self.client.force_login(self.user)

    def test_exige_login(self):
        """Sem login, a biblioteca deve redirecionar para a tela de login."""
        self.client.logout()
        resp = self.client.get(reverse('biblioteca'))
        self.assertEqual(resp.status_code, 302)  # redirect para LOGIN_URL

    def test_biblioteca_lista_apenas_livros_do_usuario(self):
        """
        A biblioteca de um usuario NAO pode mostrar livros de outro.
        Criamos livros de dois donos e conferimos o que aparece no contexto.
        """
        outro = User.objects.create_user(username='outro', email='o@o.com', password='x')
        Livro.objects.create(usuario=self.user, titulo='Meu', status='aberto')
        Livro.objects.create(usuario=outro, titulo='Alheio', status='aberto')

        resp = self.client.get(reverse('biblioteca'))
        self.assertEqual(resp.status_code, 200)
        titulos = [item['livro'].titulo for item in resp.context['livros_com_numero']]
        self.assertIn('Meu', titulos)
        self.assertNotIn('Alheio', titulos)

    def test_capitulos_com_anotacao_aparecem(self):
        """
        Regra da biblioteca: so listamos como 'capitulo com anotacao' os
        capitulos que tem PELO MENOS UM card. Capitulo vazio nao entra.
        """
        livro = Livro.objects.create(usuario=self.user, titulo='Caso', status='aberto')
        cap1 = Capitulo.objects.create(livro=livro, numero=1)
        Capitulo.objects.create(livro=livro, numero=2)  # vazio (sem cards)
        Card.objects.create(capitulo=cap1, titulo='Pista')  # so o cap 1 tem card

        resp = self.client.get(reverse('biblioteca'))
        item = [i for i in resp.context['livros_com_numero'] if i['livro'] == livro][0]
        # Capitulo 1 entra (tem card); capitulo 2 nao (vazio)
        self.assertIn(1, item['capitulos'])
        self.assertNotIn(2, item['capitulos'])

    def test_main_page_so_mostra_aberto_e_frio(self):
        """
        A main_page (dossies ativos) deve mostrar apenas livros 'aberto' ou
        'frio' — nunca 'concluido'.
        """
        Livro.objects.create(usuario=self.user, titulo='Aberto', status='aberto')
        Livro.objects.create(usuario=self.user, titulo='Frio', status='frio')
        Livro.objects.create(usuario=self.user, titulo='Concluido', status='concluido')

        resp = self.client.get(reverse('main_page'))
        titulos = [livro.titulo for _, livro in resp.context['livros_com_numero']]
        self.assertIn('Aberto', titulos)
        self.assertIn('Frio', titulos)
        self.assertNotIn('Concluido', titulos)

    def test_numeracao_de_casos_e_estavel(self):
        """
        A numeracao do caso deve ser ESTAVEL: baseada na ordem de criacao (id),
        nao na posicao apos filtrar. Ex: se o 2o livro esta concluido e some da
        main_page, o 3o livro ainda deve manter o numero 3 (e nao virar 2).
        """
        l1 = Livro.objects.create(usuario=self.user, titulo='Primeiro', status='aberto')
        l2 = Livro.objects.create(usuario=self.user, titulo='Segundo', status='concluido')
        l3 = Livro.objects.create(usuario=self.user, titulo='Terceiro', status='aberto')

        resp = self.client.get(reverse('main_page'))
        # mapeia titulo -> numero exibido
        numeros = {livro.titulo: num for num, livro in resp.context['livros_com_numero']}
        # O 'Terceiro' deve manter o numero 3, mesmo com o 'Segundo' filtrado
        self.assertEqual(numeros['Primeiro'], 1)
        self.assertEqual(numeros['Terceiro'], 3)


# =====================================================================
#  CRIAR / EDITAR / EXCLUIR LIVRO
# =====================================================================
class CrudLivroTest(TestCase):
    """Testa criacao, edicao e exclusao de livros via views."""

    def setUp(self):
        self.user = User.objects.create_user(username='u', email='u@u.com', password='x')
        self.client.force_login(self.user)

    def test_criar_livro(self):
        """POST em criar_livro deve criar o livro associado ao usuario logado."""
        resp = self.client.post(reverse('criar_livro'), {
            'titulo': 'Novo Caso', 'descricao': 'desc', 'status': 'aberto',
        })
        self.assertEqual(resp.status_code, 302)  # redireciona para biblioteca
        livro = Livro.objects.get(titulo='Novo Caso')
        self.assertEqual(livro.usuario, self.user)

    def test_criar_livro_sem_titulo_nao_cria(self):
        """Sem titulo, nenhum livro deve ser criado (a view ignora e redireciona)."""
        self.client.post(reverse('criar_livro'), {
            'titulo': '', 'descricao': 'x', 'status': 'aberto',
        })
        self.assertEqual(Livro.objects.count(), 0)

    def test_editar_livro_altera_status_e_descricao(self):
        """editar_livro deve atualizar status e descricao do livro."""
        livro = Livro.objects.create(usuario=self.user, titulo='C', status='aberto', descricao='velha')
        self.client.post(reverse('editar_livro', args=[livro.id]), {
            'status': 'frio', 'descricao': 'nova descricao',
        })
        livro.refresh_from_db()
        self.assertEqual(livro.status, 'frio')
        self.assertEqual(livro.descricao, 'nova descricao')

    def test_excluir_livro_do_proprio_usuario(self):
        """O dono consegue excluir seu livro; a resposta JSON traz ok=True."""
        livro = Livro.objects.create(usuario=self.user, titulo='Apagar', status='aberto')
        resp = self.client.post(reverse('excluir_livro', args=[livro.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertJSONEqual(resp.content, {'ok': True})
        self.assertFalse(Livro.objects.filter(id=livro.id).exists())

    def test_nao_exclui_livro_de_outro_usuario(self):
        """
        SEGURANCA: um usuario NAO pode excluir o livro de outro.
        A view usa get_object_or_404(..., usuario=request.user), entao deve
        retornar 404 e o livro deve continuar existindo.
        """
        outro = User.objects.create_user(username='outro', email='o@o.com', password='x')
        livro_alheio = Livro.objects.create(usuario=outro, titulo='Nao e seu', status='aberto')
        resp = self.client.post(reverse('excluir_livro', args=[livro_alheio.id]))
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(Livro.objects.filter(id=livro_alheio.id).exists())


# =====================================================================
#  QUADRO (capitulos, salvar, novo capitulo)
# =====================================================================
class QuadroViewTest(TestCase):
    """Testa abertura do quadro, salvamento e criacao de capitulos."""

    def setUp(self):
        self.user = User.objects.create_user(username='u', email='u@u.com', password='x')
        self.client.force_login(self.user)
        self.livro = Livro.objects.create(usuario=self.user, titulo='Caso', status='aberto')

    def test_abrir_quadro_cria_capitulo_1(self):
        """
        Abrir o quadro de um livro sem capitulos deve CRIAR o capitulo 1
        automaticamente (get_or_create). Assim nunca ha quadro sem capitulo.
        """
        self.assertEqual(self.livro.capitulos.count(), 0)
        resp = self.client.get(reverse('quadro', args=[self.livro.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(self.livro.capitulos.filter(numero=1).exists())

    def test_novo_capitulo_incrementa_numero(self):
        """novo_capitulo deve criar o proximo numero sequencial (1 -> 2)."""
        Capitulo.objects.create(livro=self.livro, numero=1)
        self.client.post(reverse('novo_capitulo', args=[self.livro.id]))
        self.assertTrue(self.livro.capitulos.filter(numero=2).exists())

    def test_salvar_quadro_cria_cards_e_conexoes(self):
        """
        salvar_quadro recebe JSON com cards (id temporario negativo) e conexoes,
        e deve cria-los no banco, traduzindo os ids temporarios para reais.
        """
        cap = Capitulo.objects.create(livro=self.livro, numero=1)
        payload = {
            'cards': [
                {'id': '-1', 'titulo': 'Suspeito', 'descricao': 'alibi', 'x': 100, 'y': 120, 'subtitulos': []},
                {'id': '-2', 'titulo': 'Arma',     'descricao': 'faca',  'x': 300, 'y': 200, 'subtitulos': []},
            ],
            'conexoes': [{'origem': '-1', 'destino': '-2'}],
        }
        resp = self.client.post(
            reverse('salvar_quadro', args=[cap.id]),
            data=json.dumps(payload), content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(cap.cards.count(), 2)
        self.assertEqual(cap.conexoes.count(), 1)
        # A conexao deve ligar os dois cards criados
        con = cap.conexoes.first()
        self.assertEqual({con.origem.titulo, con.destino.titulo}, {'Suspeito', 'Arma'})

    def test_salvar_quadro_grava_subtitulos(self):
        """
        Card de imagem manda subtitulos como lista [{titulo, conteudo}].
        Eles devem virar registros Subtitulo ligados ao card.
        """
        cap = Capitulo.objects.create(livro=self.livro, numero=1)
        payload = {
            'cards': [{
                'id': '-1', 'titulo': 'Diagrama', 'descricao': '', 'x': 50, 'y': 50,
                'subtitulos': [
                    {'titulo': 'SUSPEITO', 'conteudo': 'visto as 23h'},
                    {'titulo': 'LOCAL', 'conteudo': 'beco'},
                ],
            }],
            'conexoes': [],
        }
        self.client.post(
            reverse('salvar_quadro', args=[cap.id]),
            data=json.dumps(payload), content_type='application/json'
        )
        card = cap.cards.first()
        self.assertEqual(card.subtitulos.count(), 2)
        # A ordem deve ser preservada (ordem=0 e o primeiro)
        primeiro = card.subtitulos.order_by('ordem').first()
        self.assertEqual(primeiro.titulo, 'SUSPEITO')

    def test_salvar_quadro_atualiza_card_existente(self):
        """
        Card com id REAL (positivo) deve ser ATUALIZADO no lugar, nao recriado.
        Garante que a logica de update (que preserva a imagem) funciona.
        """
        cap = Capitulo.objects.create(livro=self.livro, numero=1)
        card = Card.objects.create(capitulo=cap, titulo='Antigo', descricao='x', pos_x=10, pos_y=10)
        payload = {
            'cards': [{
                'id': str(card.id), 'titulo': 'Atualizado', 'descricao': 'nova',
                'x': 500, 'y': 600, 'subtitulos': [],
            }],
            'conexoes': [],
        }
        self.client.post(
            reverse('salvar_quadro', args=[cap.id]),
            data=json.dumps(payload), content_type='application/json'
        )
        card.refresh_from_db()
        self.assertEqual(card.titulo, 'Atualizado')
        self.assertEqual(card.pos_x, 500)
        # Continua sendo o MESMO card (mesmo id), nao um novo
        self.assertEqual(cap.cards.count(), 1)

    def test_salvar_quadro_remove_card_apagado_na_tela(self):
        """
        Se um card existente nao vem mais no payload, ele foi apagado na tela
        e deve ser removido do banco.
        """
        cap = Capitulo.objects.create(livro=self.livro, numero=1)
        manter = Card.objects.create(capitulo=cap, titulo='Manter')
        Card.objects.create(capitulo=cap, titulo='Remover')  # esse nao vem no payload
        payload = {
            'cards': [{'id': str(manter.id), 'titulo': 'Manter', 'descricao': '', 'x': 0, 'y': 0, 'subtitulos': []}],
            'conexoes': [],
        }
        self.client.post(
            reverse('salvar_quadro', args=[cap.id]),
            data=json.dumps(payload), content_type='application/json'
        )
        self.assertEqual(cap.cards.count(), 1)
        self.assertTrue(cap.cards.filter(id=manter.id).exists())

    def test_nao_abre_quadro_de_livro_alheio(self):
        """SEGURANCA: nao se pode abrir o quadro de um livro de outro usuario."""
        outro = User.objects.create_user(username='outro', email='o@o.com', password='x')
        livro_alheio = Livro.objects.create(usuario=outro, titulo='X', status='aberto')
        resp = self.client.get(reverse('quadro', args=[livro_alheio.id]))
        self.assertEqual(resp.status_code, 404)


# =====================================================================
#  ARQUIVO DE EVIDENCIAS (exportar / importar)
# =====================================================================
class EvidenciasTest(TestCase):
    """
    Testa a exportacao (congelar snapshot) e importacao (recriar substituindo),
    incluindo a regra de negocio: so importa livro de mesmo titulo, e import
    SUBSTITUI as anotacoes atuais.
    """

    def setUp(self):
        self.autor = User.objects.create_user(username='autor', email='a@a.com', password='x')
        self.leitor = User.objects.create_user(username='leitor', email='l@l.com', password='x')

    def _livro_com_anotacoes(self, usuario, titulo='Caso X'):
        """Helper: cria um livro com 1 capitulo, 2 cards conectados e 1 subtitulo."""
        livro = Livro.objects.create(usuario=usuario, titulo=titulo, status='aberto')
        cap = Capitulo.objects.create(livro=livro, numero=1)
        a = Card.objects.create(capitulo=cap, titulo='A', descricao='card a', pos_x=10, pos_y=10)
        b = Card.objects.create(capitulo=cap, titulo='B', descricao='card b', pos_x=20, pos_y=20)
        Subtitulo.objects.create(card=a, titulo='sub', conteudo='conteudo', ordem=0)
        Conexao.objects.create(capitulo=cap, origem=a, destino=b)
        return livro

    def test_exportar_cria_anotacao_compartilhada(self):
        """
        Exportar deve criar 1 AnotacaoCompartilhada com o titulo do livro,
        o autor correto e a contagem de capitulos no snapshot.
        """
        self.client.force_login(self.autor)
        livro = self._livro_com_anotacoes(self.autor, 'Caso Exportado')
        resp = self.client.post(reverse('exportar_anotacoes'), {
            'livro_id': livro.id, 'detalhes': 'minhas notas',
        })
        self.assertEqual(resp.status_code, 302)
        export = AnotacaoCompartilhada.objects.get(titulo_livro='Caso Exportado')
        self.assertEqual(export.autor, self.autor)
        self.assertEqual(export.qtd_capitulos, 1)
        # O snapshot deve ser uma lista (de capitulos) nao-vazia
        self.assertTrue(isinstance(export.snapshot, list))
        self.assertEqual(len(export.snapshot), 1)

    def test_importar_exige_livro_de_mesmo_titulo(self):
        """
        REGRA: so importa quem tem um livro de TITULO IGUAL. Se o leitor nao
        tem, a view recusa (ok=False) e nada e criado no acervo dele.
        """
        self.client.force_login(self.autor)
        livro = self._livro_com_anotacoes(self.autor, 'Titulo Unico')
        self.client.post(reverse('exportar_anotacoes'), {'livro_id': livro.id, 'detalhes': ''})
        export = AnotacaoCompartilhada.objects.get(titulo_livro='Titulo Unico')

        # leitor NAO tem livro com esse titulo
        self.client.force_login(self.leitor)
        resp = self.client.post(reverse('importar_anotacoes', args=[export.id]))
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Capitulo.objects.filter(livro__usuario=self.leitor).count(), 0)

    def test_importar_copia_anotacoes_para_livro_de_mesmo_titulo(self):
        """
        Se o leitor TEM um livro de mesmo titulo, importar recria os capitulos,
        cards, subtitulos e conexoes no livro dele.
        """
        # autor exporta
        self.client.force_login(self.autor)
        livro_autor = self._livro_com_anotacoes(self.autor, 'Compartilhado')
        self.client.post(reverse('exportar_anotacoes'), {'livro_id': livro_autor.id, 'detalhes': ''})
        export = AnotacaoCompartilhada.objects.get(titulo_livro='Compartilhado')

        # leitor tem um livro VAZIO de mesmo titulo
        livro_leitor = Livro.objects.create(usuario=self.leitor, titulo='Compartilhado', status='aberto')
        self.assertEqual(livro_leitor.capitulos.count(), 0)

        self.client.force_login(self.leitor)
        resp = self.client.post(reverse('importar_anotacoes', args=[export.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertJSONEqual(resp.content, {'ok': True})

        # O livro do leitor agora tem o capitulo, os 2 cards, o subtitulo e a conexao
        livro_leitor.refresh_from_db()
        self.assertEqual(livro_leitor.capitulos.count(), 1)
        cap = livro_leitor.capitulos.first()
        self.assertEqual(cap.cards.count(), 2)
        self.assertEqual(cap.conexoes.count(), 1)
        self.assertEqual(Subtitulo.objects.filter(card__capitulo=cap).count(), 1)

    def test_importar_substitui_anotacoes_existentes(self):
        """
        REGRA (sua escolha): importar SUBSTITUI as anotacoes atuais do livro.
        Aqui o leitor ja tem um capitulo proprio; apos importar (1 capitulo no
        snapshot), ele deve ficar com as anotacoes do snapshot, nao com as antigas.
        """
        self.client.force_login(self.autor)
        livro_autor = self._livro_com_anotacoes(self.autor, 'Substituir')
        self.client.post(reverse('exportar_anotacoes'), {'livro_id': livro_autor.id, 'detalhes': ''})
        export = AnotacaoCompartilhada.objects.get(titulo_livro='Substituir')

        # leitor tem o mesmo titulo, mas com anotacoes DIFERENTES (2 capitulos antigos)
        livro_leitor = Livro.objects.create(usuario=self.leitor, titulo='Substituir', status='aberto')
        cap_antigo1 = Capitulo.objects.create(livro=livro_leitor, numero=1)
        Capitulo.objects.create(livro=livro_leitor, numero=2)
        Card.objects.create(capitulo=cap_antigo1, titulo='CARD ANTIGO')

        self.client.force_login(self.leitor)
        self.client.post(reverse('importar_anotacoes', args=[export.id]))

        livro_leitor.refresh_from_db()
        # O snapshot tinha 1 capitulo -> o leitor deve ter exatamente 1 agora (os 2 antigos sumiram)
        self.assertEqual(livro_leitor.capitulos.count(), 1)
        # E o card antigo nao pode mais existir
        self.assertFalse(Card.objects.filter(titulo='CARD ANTIGO').exists())
