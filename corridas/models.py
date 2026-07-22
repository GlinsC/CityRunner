from django.db import models

# Create your models here.
class Corrida(models.Model):
    nome = models.CharField(max_length=100)
    local_inicio = models.CharField(max_length=100)
    local_fim = models.CharField(max_length=100)
    distancia = models.FloatField()
    descricao = models.TextField()
    origem_latitude = models.FloatField(null=True, blank=True)
    origem_longitude = models.FloatField(null=True, blank=True)
    destino_latitude = models.FloatField(null=True, blank=True)
    destino_longitude = models.FloatField(null=True, blank=True)

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
    
class usuario(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    senha = models.CharField(max_length=100)
    admin = models.BooleanField(default=False)

    def __str__(self):
        return self.nome
    
class UsuarioCorrida(models.Model):
    usuario = models.ForeignKey(
        usuario,
        on_delete=models.CASCADE,
        related_name="corridas"
    )
    corrida = models.ForeignKey(
        Corrida,
        on_delete=models.CASCADE,
        related_name="usuarios"
    )

    def __str__(self):
        return f"{self.usuario.nome} - {self.corrida.nome}"
    
class UsuarioComentario(models.Model):
    usuario = models.ForeignKey(
        usuario,
        on_delete=models.CASCADE,
        related_name="comentarios"
    )
    comentario = models.ForeignKey(
        ComentarioCorrida,
        on_delete=models.CASCADE,
        related_name="usuarios"
    )

    def __str__(self):
        return f"{self.usuario.nome} - {self.comentario.avaliacao}⭐"
    
class rankingPaceCorrida(models.Model):
    corrida = models.ForeignKey(
        Corrida,
        on_delete=models.CASCADE,
        related_name="rankings"
    )
    usuario = models.ForeignKey(
        usuario,
        on_delete=models.CASCADE,
        related_name="rankings"
    )
    pace = models.FloatField()

    def __str__(self):
        return f"{self.corrida.nome} - {self.usuario.nome} - {self.pace} min/km"
    