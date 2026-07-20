import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt

from .models import ComentarioCorrida, Corrida


# Métodos de visualização HTML

def corrida_list(request):
    corridas = Corrida.objects.all().order_by("id")
    return render(request, "corrida_list.html", {"corridas": corridas})


# Métodos da API JSON
@csrf_exempt
def corrida_api_list(request):
    corrida_data = list(
        Corrida.objects.values(
            "id",
            "nome",
            "local_inicio",
            "local_fim",
            "distancia",
            "descricao",
            "origem_latitude",
            "origem_longitude",
            "destino_latitude",
            "destino_longitude",
        )
    )
    return JsonResponse(corrida_data, safe=False)


@csrf_exempt
def corrida_post(request):
    if request.method == "POST":
        data = json.loads(request.body)
        corrida = Corrida.objects.create(
            nome=data["nome"],
            local_inicio=data["local_inicio"],
            local_fim=data["local_fim"],
            distancia=data["distancia"],
            descricao=data["descricao"],
            origem_latitude=data["origem_latitude"],
            origem_longitude=data["origem_longitude"],
            destino_latitude=data["destino_latitude"],
            destino_longitude=data["destino_longitude"],
        )
        return JsonResponse({"id": corrida.id, "message": "Corrida criada com sucesso!"})
    return JsonResponse({"error": "Método não permitido"}, status=405)


def corrida_detail(request, corrida_id):
    corrida = get_object_or_404(Corrida, id=corrida_id)
    comentarios = corrida.comentarios.all().order_by("-id")
    return render(
        request,
        "corrida_detail.html",
        {
            "corrida": corrida,
            "comentarios": comentarios,
            "google_maps_api_key": "",
        },
    )


def corrida_detail_api(request, corrida_id):
    corrida = get_object_or_404(Corrida, id=corrida_id)
    corrida_data = {
        "id": corrida.id,
        "nome": corrida.nome,
        "local_inicio": corrida.local_inicio,
        "local_fim": corrida.local_fim,
        "distancia": corrida.distancia,
        "descricao": corrida.descricao,
        "comentarios": list(corrida.comentarios.values("id", "comentario", "avaliacao")),
    }
    return JsonResponse(corrida_data)


@csrf_exempt
def corrida_delete(request, corrida_id):
    corrida = get_object_or_404(Corrida, id=corrida_id)
    corrida.delete()
    return JsonResponse({"message": "Corrida deletada com sucesso!"})


# Métodos de comentários

def comentario_corrida_list(request, corrida_id):
    comentarios = ComentarioCorrida.objects.filter(corrida_id=corrida_id)
    comentario_data = list(comentarios.values("id", "corrida_id", "comentario", "avaliacao"))
    return JsonResponse(comentario_data, safe=False)


@csrf_exempt
def comentario_corrida_post(request, corrida_id):
    if request.method == "POST":
        data = json.loads(request.body)
        corrida = Corrida.objects.get(id=corrida_id)
        comentario = ComentarioCorrida.objects.create(
            corrida=corrida,
            comentario=data["comentario"],
            avaliacao=data["avaliacao"],
        )
        return JsonResponse({"id": comentario.id, "message": "Comentário criado com sucesso!"})
    return JsonResponse({"error": "Método não permitido"}, status=405)