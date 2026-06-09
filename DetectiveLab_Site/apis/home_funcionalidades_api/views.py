"""
Views da API do Home (autenticacao por token).

Fluxo de auth no app mobile:
  1. POST /api/auth/register/  -> cria usuario e ja devolve um token.
  2. POST /api/auth/login/     -> valida email+senha e devolve o token.
  3. O app guarda o token e manda em todo request:
        Authorization: Token <valor>
  4. POST /api/auth/logout/    -> apaga o token (exige estar autenticado).

O login por EMAIL espelha o EmailBackend do site (autentica pelo email, nao
pelo username). register e login sao AbertOS (AllowAny); o resto exige token.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token

from django.contrib.auth import get_user_model

from .serializers import RegisterSerializer, UsuarioSerializer

User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])   # registro nao exige login
def register(request):
    """
    Cria um usuario e ja devolve um token (login automatico, como na web).
    Retorna 201 com {token, user}. Em caso de dados invalidos, 400 com os erros.
    """
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UsuarioSerializer(user, context={'request': request}).data,
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])   # login nao exige login (obviamente)
def login_api(request):
    """
    Login por EMAIL + senha (espelha o EmailBackend do site).
    Corpo: { "email": "...", "password": "..." }.
    Sucesso -> 200 {token, user}. Falha -> 401.
    """
    email = (request.data.get('email') or '').strip()
    senha = request.data.get('password') or ''

    if not email or not senha:
        return Response({'erro': 'Informe email e senha.'}, status=status.HTTP_400_BAD_REQUEST)

    # Busca pelo email (login por email, como no site)
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'erro': 'Credenciais invalidas.'}, status=status.HTTP_401_UNAUTHORIZED)

    if not user.check_password(senha):
        return Response({'erro': 'Credenciais invalidas.'}, status=status.HTTP_401_UNAUTHORIZED)

    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        'token': token.key,
        'user': UsuarioSerializer(user, context={'request': request}).data,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])   # so faz logout quem esta logado
def logout_api(request):
    """Apaga o token do usuario (invalida a sessao mobile)."""
    Token.objects.filter(user=request.user).delete()
    return Response({'ok': True})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    """Retorna os dados do usuario logado (tela de perfil)."""
    return Response(UsuarioSerializer(request.user, context={'request': request}).data)