import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .models import ComentarioCorrida, Corrida

# Create your views here.

#Metodos Corrida
@csrf_exempt
def corrida_list(request):
    corridas = Corrida.objects.all()

    corrida_data = []
    corrida_data = list(
    Corrida.objects.values(
        "id",
        "nome",
        "local_inicio",
        "local_fim",
        "distancia",
        "descricao"
        )
    )
    return JsonResponse(corrida_data, safe=False)

@csrf_exempt
def corrida_post(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        corrida = Corrida.objects.create(
            nome=data['nome'],
            local_inicio=data['local_inicio'],
            local_fim=data['local_fim'],
            distancia=data['distancia'],
            descricao=data['descricao'],
        )
        return JsonResponse({'id': corrida.id, 'message': 'Corrida criada com sucesso!'})
    else:
        return JsonResponse({'error': 'Método não permitido'}, status=405)

def corrida_detail(request, corrida_id):
    try:
        corrida = Corrida.objects.get(id=corrida_id)
        corrida_data = {
            "id": corrida.id,
            "nome": corrida.nome,
            "local_inicio": corrida.local_inicio,
            "local_fim": corrida.local_fim,
            "distancia": corrida.distancia,
            "descricao": corrida.descricao,
            "comentarios": list(corrida.comentarios.values("id", "comentario", "avaliacao"))
        }
        return JsonResponse(corrida_data)
    except Corrida.DoesNotExist:
        return JsonResponse({'error': 'Corrida não encontrada'}, status=404)
    

#Metodos ComentarioCorrida

def comentario_corrida_list(request, corrida_id):
    comentarios = ComentarioCorrida.objects.filter(corrida_id=corrida_id)
    comentario_data = list(
        comentarios.values(
            "id",
            "corrida_id",
            "comentario",
            "avaliacao"
        )
    )
    return JsonResponse(comentario_data, safe=False)

@csrf_exempt
def comentario_corrida_post(request, corrida_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        corrida = Corrida.objects.get(id=corrida_id)
        comentario = ComentarioCorrida.objects.create(
            corrida=corrida,
            comentario=data['comentario'],
            avaliacao=data['avaliacao']
        )
        return JsonResponse({'id': comentario.id, 'message': 'Comentário criado com sucesso!'})
    else:
        return JsonResponse({'error': 'Método não permitido'}, status=405)