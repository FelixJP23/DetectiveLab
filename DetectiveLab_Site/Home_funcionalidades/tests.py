"""
Testes unitarios do app Home_funcionalidades (autenticacao).

COMO ESTES TESTES FUNCIONAM
---------------------------
Cada classe agrupa testes de uma area. O Django cria um banco de dados
temporario e isolado para os testes (nada toca o seu banco real), e cada
metodo `test_*` roda numa transacao que e desfeita ao final — entao um teste
nunca afeta o outro.

Usamos:
- `TestCase`        : classe base do Django (cria o banco de teste, da acesso ao self.client).
- `self.client`     : um navegador-falso que faz requisicoes (GET/POST) sem subir servidor.
- `get_user_model()`: pega o seu modelo de usuario customizado (Usuario_customizado)
                      sem precisar importa-lo diretamente — funciona mesmo se o caminho mudar.
- `reverse('nome')` : converte o NOME da rota (do urls.py) na URL real. Se voce mudar a URL
                      mas manter o name, o teste continua valido.

Para rodar:  python manage.py test Home_funcionalidades
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class ModeloUsuarioTest(TestCase):
    """Verifica o modelo de usuario customizado."""

    def test_cria_usuario_com_campos_basicos(self):
        """
        Um usuario deve ser criavel com username, email e senha, e a senha
        deve ser ARMAZENADA COM HASH (nunca em texto puro). Se alguem trocar
        create_user por uma criacao manual sem hash, este teste quebra.
        """
        user = User.objects.create_user(
            username='detetive', email='detetive@noir.com', password='segredo123'
        )
        self.assertEqual(user.username, 'detetive')
        self.assertEqual(user.email, 'detetive@noir.com')
        # A senha guardada nao pode ser igual ao texto digitado (tem que ser hash)
        self.assertNotEqual(user.password, 'segredo123')
        # E precisa validar corretamente via check_password
        self.assertTrue(user.check_password('segredo123'))

    def test_campo_foto_opcional(self):
        """O campo `foto` e opcional (blank/null). Criar sem foto nao pode dar erro."""
        user = User.objects.create_user(username='semfoto', email='s@s.com', password='x')
        # Sem foto, o campo deve ser "vazio" (falsy)
        self.assertFalse(user.foto)


class RegistroTest(TestCase):
    """Testa a view de registro de novos usuarios."""

    def test_get_pagina_registro_carrega(self):
        """A pagina de registro deve responder 200 (OK) num GET."""
        resp = self.client.get(reverse('Register'))
        self.assertEqual(resp.status_code, 200)

    def test_registro_cria_usuario_e_loga(self):
        """
        Um POST valido no registro deve:
          1. criar o usuario no banco,
          2. autenticar (logar) o usuario automaticamente,
          3. redirecionar para a main_page.

        Este e o teste que pega o bug do 'backend' que voce teve: se o
        login() apos o registro nao passar o backend explicito, a requisicao
        levanta ValueError e o status NAO sera 302 — entao o teste falha.
        """
        resp = self.client.post(reverse('Register'), {
            'username': 'novato',
            'email': 'novato@noir.com',
            'password1': 'SenhaForte!2024',
            'password2': 'SenhaForte!2024',
        })
        # O usuario foi criado?
        self.assertTrue(User.objects.filter(username='novato').exists())
        # Houve redirect (302) apos registrar?
        self.assertEqual(resp.status_code, 302)
        # O usuario ficou autenticado na sessao? (login automatico funcionou)
        self.assertIn('_auth_user_id', self.client.session)

    def test_registro_com_senhas_diferentes_falha(self):
        """
        Se as duas senhas nao batem, o usuario NAO pode ser criado.
        A pagina deve apenas re-renderizar (200), sem redirect.
        """
        resp = self.client.post(reverse('Register'), {
            'username': 'erro',
            'email': 'erro@noir.com',
            'password1': 'umaSenha123',
            'password2': 'outraSenha456',
        })
        self.assertFalse(User.objects.filter(username='erro').exists())
        self.assertEqual(resp.status_code, 200)  # ficou na mesma pagina (form invalido)


class LoginPorEmailTest(TestCase):
    """
    Testa o login por E-MAIL (seu EmailBackend), nao por username.
    """

    def setUp(self):
        """setUp roda ANTES de cada teste desta classe, criando um usuario base."""
        self.user = User.objects.create_user(
            username='marlowe', email='marlowe@noir.com', password='cidade1940'
        )

    def test_login_com_email_funciona(self):
        """
        O usuario deve conseguir logar usando o EMAIL no campo de usuario.
        Como o LoginView usa EmailLoginForm + EmailBackend, o campo enviado
        chama-se 'username' mas recebe o email.
        """
        resp = self.client.post(reverse('login'), {
            'username': 'marlowe@noir.com',   # email no lugar do username
            'password': 'cidade1940',
        })
        # Login certo redireciona (302) para LOGIN_REDIRECT_URL (main_page)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('_auth_user_id', self.client.session)

    def test_login_com_senha_errada_falha(self):
        """Senha errada nao loga: sem sessao e a pagina volta com 200."""
        resp = self.client.post(reverse('login'), {
            'username': 'marlowe@noir.com',
            'password': 'senhaerrada',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)


class LogoutTest(TestCase):
    """Testa o logout."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='spade', email='spade@noir.com', password='falcao1941'
        )

    def test_logout_encerra_sessao(self):
        """
        Apos logar e dar logout (POST), a sessao do usuario deve ser encerrada.
        O logout do Django e POST-only, por isso usamos self.client.post.
        """
        self.client.force_login(self.user)
        self.assertIn('_auth_user_id', self.client.session)  # esta logado
        self.client.post(reverse('logout'))
        self.assertNotIn('_auth_user_id', self.client.session)  # saiu


