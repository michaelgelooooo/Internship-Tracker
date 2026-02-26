from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("auth/", views.auth, name="auth"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),

    path("update-log/", views.update_daily_record, name="update-log"),
    path("mark-day/", views.mark_day, name="mark-day"),
]
