from django.urls import path

from app import views


urlpatterns = [
    path("", views.index, name="index"),
    path("health", views.health_check, name="health"),
    path("chat", views.chat, name="chat"),
    path("api/health", views.health_check, name="api-health"),
    path("api/chat", views.chat, name="api-chat"),
    path("api/feedback", views.feedback, name="api-feedback"),
    path("feedback/stats", views.feedback_stats, name="feedback-stats"),
]
