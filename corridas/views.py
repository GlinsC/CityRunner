import json
import os
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import jwt
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .models import ComentarioCorrida, Corrida, UsuarioComentario, rankingPaceCorrida, usuario

JWT_SECRET = os.environ.get("CITYRUNNER_JWT_SECRET", "cityrunner-secret")
JWT_TTL_HOURS = 8


# Métodos de visualização HTML

def get_authenticated_user(request):
    auth_header = request.headers.get("Authorization", "")
    token = None

    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
    elif request.session.get("access_token"):
        token = request.session.get("access_token")

    if not token:
        return None

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if not user_id:
            return None
        return usuario.objects.get(id=user_id)
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, usuario.DoesNotExist):
        return None


def require_auth(view_func):
    def wrapped(request, *args, **kwargs):
        user = get_authenticated_user(request)
        if not user:
            return JsonResponse({"error": "Autenticação necessária."}, status=401)
        request.user = user
        return view_func(request, *args, **kwargs)
    return wrapped


def is_authenticated_request(request):
    if request.session.get("access_token") or request.session.get("usuario_id"):
        token = request.session.get("access_token")
        if token:
            try:
                jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
                return True
            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
                return False
        return True

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            return bool(payload.get("user_id"))
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return False

    return False


def corrida_list(request):
    if not is_authenticated_request(request):
        next_url = request.get_full_path()
        login_url = reverse("login")
        return redirect(f"{login_url}?{urlencode({'next': next_url})}")

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
@require_auth
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
    if not is_authenticated_request(request):
        next_url = request.get_full_path()
        login_url = reverse("login")
        return redirect(f"{login_url}?{urlencode({'next': next_url})}")

    corrida = get_object_or_404(Corrida, id=corrida_id)
    comentarios = corrida.comentarios.all().order_by("-id")
    rankings = rankingPaceCorrida.objects.filter(corrida=corrida).select_related("usuario").order_by("pace", "id")
    return render(
        request,
        "corrida_detail.html",
        {
            "corrida": corrida,
            "comentarios": comentarios,
            "rankings": rankings,
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
@require_auth
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
@require_auth
def comentario_corrida_post(request, corrida_id):
    if request.method != "POST":
        return JsonResponse({"error": "Método não permitido"}, status=405)

    if request.content_type and "application/json" in request.content_type:
        try:
            data = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON inválido"}, status=400)
    else:
        data = request.POST

    comentario_texto = data.get("comentario") or data.get("comentario_texto")
    avaliacao = data.get("avaliacao")

    if not comentario_texto:
        return JsonResponse({"error": "comentario é obrigatório."}, status=400)
    if avaliacao is None:
        return JsonResponse({"error": "avaliacao é obrigatória."}, status=400)

    try:
        avaliacao_value = float(avaliacao)
    except (TypeError, ValueError):
        return JsonResponse({"error": "avaliacao deve ser numérica."}, status=400)

    corrida = get_object_or_404(Corrida, id=corrida_id)
    comentario = ComentarioCorrida.objects.create(
        corrida=corrida,
        comentario=comentario_texto,
        avaliacao=avaliacao_value,
    )
    UsuarioComentario.objects.create(usuario=request.user, comentario=comentario)

    return JsonResponse({
        "id": comentario.id,
        "message": "Comentário criado com sucesso!",
        "userName": request.user.nome,
    }, status=201)

@csrf_exempt
@require_auth
def comentario_corrida_delete(request, corrida_id, comentario_id):
    comentario = get_object_or_404(ComentarioCorrida, id=comentario_id, corrida_id=corrida_id)
    comentario.delete()
    return JsonResponse({"message": "Comentário deletado com sucesso!"})

# Métodos de ranking de pace

def ranking_pace(request):
    rankings = rankingPaceCorrida.objects.select_related("corrida", "usuario").all().order_by("pace", "id")
    ranking = [
        {
            "id": entry.id,
            "corrida_id": entry.corrida_id,
            "corrida": entry.corrida.nome,
            "usuario_id": entry.usuario_id,
            "usuario": entry.usuario.nome,
            "pace": entry.pace,
        }
        for entry in rankings
    ]
    return JsonResponse(ranking, safe=False)


@csrf_exempt
@require_auth
def ranking_pace_post(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método não permitido"}, status=405)

    if request.content_type and "application/json" in request.content_type:
        try:
            data = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON inválido"}, status=400)
    else:
        data = request.POST

    corrida_id = data.get("corrida_id") or data.get("corrida") or data.get("corridaId")
    usuario_id = data.get("usuario_id") or data.get("usuario") or data.get("usuarioId")
    pace = data.get("pace")

    if not corrida_id:
        return JsonResponse({"error": "corrida_id é obrigatório."}, status=400)
    if pace is None:
        return JsonResponse({"error": "pace é obrigatório."}, status=400)

    try:
        pace_value = float(pace)
    except (TypeError, ValueError):
        return JsonResponse({"error": "pace deve ser numérico."}, status=400)

    corrida = get_object_or_404(Corrida, id=corrida_id)

    if usuario_id:
        usuario_obj = get_object_or_404(usuario, id=usuario_id)
    else:
        usuario_obj = request.user

    existing_entry = rankingPaceCorrida.objects.filter(corrida=corrida, usuario=usuario_obj).order_by("pace", "id").first()
    if existing_entry and existing_entry.pace <= pace_value:
        return JsonResponse({
            "id": existing_entry.id,
            "corrida_id": corrida.id,
            "corrida": corrida.nome,
            "usuario_id": usuario_obj.id,
            "usuario": usuario_obj.nome,
            "pace": existing_entry.pace,
        }, status=200)

    if existing_entry:
        existing_entry.pace = pace_value
        existing_entry.save(update_fields=["pace"])
        ranking_entry = existing_entry
    else:
        ranking_entry = rankingPaceCorrida.objects.create(corrida=corrida, usuario=usuario_obj, pace=pace_value)

    return JsonResponse(
        {
            "id": ranking_entry.id,
            "corrida_id": corrida.id,
            "corrida": corrida.nome,
            "usuario_id": usuario_obj.id,
            "usuario": usuario_obj.nome,
            "pace": ranking_entry.pace,
        },
        status=201,
    )


# Métodos de usuário

def usuario_list(request):
    usuarios = usuario.objects.all().order_by("id")
    usuario_data = list(usuarios.values("id", "nome", "email"))
    return JsonResponse(usuario_data, safe=False)


@csrf_exempt
def usuario_post(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método não permitido"}, status=405)

    if request.content_type and "application/json" in request.content_type:
        data = json.loads(request.body.decode("utf-8") or "{}")
    else:
        data = request.POST

    usuario_obj = usuario.objects.create(
        nome=data.get("nome", ""),
        email=data.get("email", ""),
        senha=data.get("senha", ""),
    )
    return JsonResponse({"id": usuario_obj.id, "message": "Usuário criado com sucesso!"}, status=201)


def usuario_delete(request, usuario_id):
    usuario_obj = get_object_or_404(usuario, id=usuario_id)
    usuario_obj.delete()
    return JsonResponse({"message": "Usuário deletado com sucesso!"})


def usuario_detail(request, usuario_id):
    usuario_obj = get_object_or_404(usuario, id=usuario_id)
    usuario_data = {
        "id": usuario_obj.id,
        "nome": usuario_obj.nome,
        "email": usuario_obj.email,
        "paces": list(usuario_obj.rankingpacecorrida_set.values("id", "corrida_id", "pace")),
    }
    return JsonResponse(usuario_data)


def login_view(request):
    next_url = request.POST.get("next") or request.GET.get("next") or reverse("corrida_list")

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        senha = request.POST.get("senha", "")
        user = usuario.objects.filter(email=email, senha=senha).first()
        if user:
            expires_at = datetime.now(timezone.utc) + timedelta(hours=JWT_TTL_HOURS)
            token = jwt.encode({
                "user_id": user.id,
                "email": user.email,
                "exp": int(expires_at.timestamp()),
            }, JWT_SECRET, algorithm="HS256")
            request.session["usuario_id"] = user.id
            request.session["usuario_nome"] = user.nome
            request.session["access_token"] = token
            messages.success(request, f"Bem-vindo(a), {user.nome}!")
            return render(request, "login.html", {"token": token, "redirect_to": next_url, "next": next_url})
        messages.error(request, "Email ou senha inválidos.")

    return render(request, "login.html", {"next": next_url})


def register_view(request):
    next_url = request.POST.get("next") or request.GET.get("next") or reverse("corrida_list")

    if request.method == "POST":
        nome = request.POST.get("nome", "").strip()
        email = request.POST.get("email", "").strip()
        senha = request.POST.get("senha", "")

        if not nome or not email or not senha:
            messages.error(request, "Preencha todos os campos.")
        elif usuario.objects.filter(email=email).exists():
            messages.error(request, "Este e-mail já está cadastrado.")
        else:
            user = usuario.objects.create(nome=nome, email=email, senha=senha)
            expires_at = datetime.now(timezone.utc) + timedelta(hours=JWT_TTL_HOURS)
            token = jwt.encode({
                "user_id": user.id,
                "email": user.email,
                "exp": int(expires_at.timestamp()),
            }, JWT_SECRET, algorithm="HS256")
            request.session["usuario_id"] = user.id
            request.session["usuario_nome"] = user.nome
            request.session["access_token"] = token
            messages.success(request, f"Conta criada com sucesso, {user.nome}!")
            return render(request, "register.html", {"token": token, "redirect_to": next_url, "next": next_url})

    return render(request, "register.html", {"next": next_url})


def logout_view(request):
    request.session.flush()
    messages.success(request, "Você saiu da conta.")
    return redirect("login")