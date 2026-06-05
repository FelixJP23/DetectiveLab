from django.db import models
from django.conf import settings

class Livro(models.Model):
    STATUS_CHOICES = [
        ('aberto',   'Aberto'),
        ('frio',     'Frio'),
        ('concluido','Concluído'),
    ]

    usuario  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='livros'
    )
    titulo   = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    capa     = models.ImageField(upload_to='capas_livros/', blank=True, null=True)
    status   = models.CharField(max_length=10, choices=STATUS_CHOICES, default='aberto')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']
        verbose_name = 'Livro'
        verbose_name_plural = 'Livros'

    def __str__(self):
        return self.titulo