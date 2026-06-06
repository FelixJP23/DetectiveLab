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
    


class Capitulo(models.Model):
    livro     = models.ForeignKey(Livro, on_delete=models.CASCADE, related_name='capitulos')
    numero    = models.PositiveIntegerField()          # 1, 2, 3...
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['numero']
        unique_together = ('livro', 'numero')

    def __str__(self):
        return f'{self.livro.titulo} - Capitulo {self.numero}'


class Card(models.Model):
    capitulo  = models.ForeignKey(Capitulo, on_delete=models.CASCADE, related_name='cards')
    titulo    = models.CharField(max_length=200, blank=True)
    descricao = models.TextField(blank=True)
    imagem    = models.ImageField(upload_to='cards_ocr/', blank=True, null=True)  # <- novo
    pos_x     = models.IntegerField(default=100)
    pos_y     = models.IntegerField(default=100)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.titulo or f'Card {self.id}'


class Conexao(models.Model):
    capitulo = models.ForeignKey(Capitulo, on_delete=models.CASCADE, related_name='conexoes')
    origem   = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='conexoes_origem')
    destino  = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='conexoes_destino')

    class Meta:
        unique_together = ('origem', 'destino')


class Subtitulo(models.Model):
    card      = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='subtitulos')
    titulo    = models.CharField(max_length=300, blank=True)   # o texto do OCR (editavel)
    conteudo  = models.TextField(blank=True)                   # o que o usuario escreve
    ordem     = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordem', 'id']