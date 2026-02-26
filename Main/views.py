from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Internship


@login_required
def index(request):
    return render(request, "pages/index.html")


def auth(request):
    if request.user.is_authenticated:
        return redirect("index")

    active_tab = request.GET.get("tab", "login")

    return render(request, "pages/auth.html", {"active_tab": active_tab})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("index")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect("index")
        else:
            # Tag this error as login-specific
            messages.error(request, "Invalid username or password.")
            return redirect("/auth/?tab=login")

    return redirect("auth")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("index")

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        company_name = request.POST.get("company_name")
        supervisor_name = request.POST.get("supervisor_name")
        start_date = request.POST.get("start_date")
        total_hours_required = request.POST.get("total_hours_required")

        # Validation
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("/auth/?tab=register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("/auth/?tab=register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect("/auth/?tab=register")

        # Create user
        user = User.objects.create_user(
            username=username, email=email, password=password1
        )

        # Create internship record
        Internship.objects.create(
            user=user,
            company_name=company_name,
            supervisor_name=supervisor_name,
            start_date=start_date,
            total_hours_required=total_hours_required,
        )

        login(request, user)
        return redirect("index")

    return redirect("auth")


def logout_view(request):
    logout(request)

    return redirect("auth")
