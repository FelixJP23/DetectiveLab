from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario_customizado
from django.contrib.auth.forms import AuthenticationForm
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
    


class EmailLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'placeholder': 'voce@exemplo.com'})
    )