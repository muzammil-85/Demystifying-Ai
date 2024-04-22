from django.urls import path
from . import views

urlpatterns = [
    path('chatbot', views.chatbot, name='chatbot'),
    path('explain', views.explain_shap, name='explain'),
    path('download_video/', views.download_video, name='download_video'),
    path('', views.login, name='login'),
    path('register', views.register, name='register'),
    path('logout', views.logout, name='logout'),
]