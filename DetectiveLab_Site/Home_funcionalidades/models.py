from django.db import models
from django.contrib.auth.models import AbstractUser



class Usuario_customizado(AbstractUser):

    foto = models.ImageField(upload_to='fotos_usuarios/',blank=True,null=True)
    