from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario_customizado

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    foto = forms.ImageField(required=False)   

    class Meta:
        model = Usuario_customizado          
        fields = ['username', 'email', 'foto', 'password1', 'password2']  

    def clean_email(self):                    
        email = self.cleaned_data.get('email')
        if Usuario_customizado.objects.filter(email=email).exists():
            raise forms.ValidationError('Este e-mail já está cadastrado.')
        return email