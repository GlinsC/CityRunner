from django.urls import path

from . import views


urlpatterns = [
    # Rotas HTML da aplicação
    path('', views.corrida_list, name='corrida_list'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('<int:corrida_id>/', views.corrida_detail, name='corrida_detail'),

    # Rotas da API JSON
    path('api/', views.corrida_api_list, name='corrida_api_list'),
    path('post/', views.corrida_post, name='corrida_post'),
    path('api/<int:corrida_id>/', views.corrida_detail_api, name='corrida_detail_api'),
    path('<int:corrida_id>/delete/', views.corrida_delete, name='corrida_delete'),

    # Rotas para comentários
    path('comentarios/<int:corrida_id>/', views.comentario_corrida_list, name='comentario_corrida_list'),
    path('comentarios/<int:corrida_id>/post/', views.comentario_corrida_post, name='comentario_corrida_post'),
    path('comentarios/<int:corrida_id>/<int:comentario_id>/delete/', views.comentario_corrida_delete, name='comentario_corrida_delete'),

    # Ranking de pace
    path('rankings/pace/', views.ranking_pace, name='ranking_pace'),
    path('rankings/pace/post/', views.ranking_pace_post, name='ranking_pace_post'),

    # Usuários
    path('usuarios/', views.usuario_list, name='usuario_list'),
    path('usuarios/post/', views.usuario_post, name='usuario_post'),
    path('usuarios/<int:usuario_id>/', views.usuario_detail, name='usuario_detail'),
    path('usuarios/<int:usuario_id>/delete/', views.usuario_delete, name='usuario_delete'),
]