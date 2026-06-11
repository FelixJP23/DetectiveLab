"""
Serializers do Home (API): registro de usuario e dados do usuario.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """
    Registro de usuario via API. Espelha o RegisterForm web:
    - exige username, email e senha;
    - valida a senha com os validadores do Django;
    - confirma password == password2;
    - foto opcional.
    A senha e gravada com hash (create_user).
    """
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'foto', 'password', 'password2']
        extra_kwargs = {
            'email': {'required': True},
            'foto': {'required': False},
        }

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password2'):
            raise serializers.ValidationError({'password2': 'As senhas nao conferem.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2', None)
        senha = validated_data.pop('password')
        foto = validated_data.pop('foto', None)
        user = User(**validated_data)
        user.set_password(senha)   # hash da senha
        if foto:
            user.foto = foto
        user.save()
        return user


class UsuarioSerializer(serializers.ModelSerializer):
    """Dados publicos do usuario logado (para a tela de perfil do app)."""
    foto_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'foto_url']

    def get_foto_url(self, obj):
        if not obj.foto:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(obj.foto.url) if request else obj.foto.url