from django.db import models

# Create your models here.
class Corrida(models.Model):
    nome = models.CharField(max_length=100)
    local_inicio = models.CharField(max_length=100)
    local_fim = models.CharField(max_length=100)
    distancia = models.FloatField()
    descricao = models.TextField()

    def __str__(self):
        return self.nome


class ComentarioCorrida(models.Model):
    corrida = models.ForeignKey(
        Corrida,
        on_delete=models.CASCADE,
        related_name="comentarios"
    )

    comentario = models.TextField()
    avaliacao = models.FloatField()

    def __str__(self):
        return f"{self.corrida.nome} - {self.avaliacao}⭐"
    