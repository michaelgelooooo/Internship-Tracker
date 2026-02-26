from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from datetime import date
from calendar import monthrange
from .models import Internship, DailyTimeRecord


# -----------------------------
# 1️⃣ Internship Statistics
# -----------------------------
def get_internship_stats(internship):
    total_logged = internship.total_hours_logged
    total_required = internship.total_hours_required
    remaining_hours = max(total_required - total_logged, 0)

    percent_complete = (
        int((total_logged / total_required) * 100) if total_required else 0
    )

    return {
        "total_logged": total_logged,
        "total_required": total_required,
        "remaining_hours": remaining_hours,
        "percent_complete": percent_complete,
        "percent_remaining": 100 - percent_complete,
    }


# -----------------------------
# 2️⃣ Month Data
# -----------------------------
def get_current_month_data():
    today = date.today()
    first_day_of_month = today.replace(day=1)
    _, last_day = monthrange(today.year, today.month)

    return {
        "today": today,
        "current_month": today.strftime("%B %Y"),
        "first_day_of_month": first_day_of_month,
        "days_in_month": list(range(1, last_day + 1)),
    }


def get_daily_rows(internship, today):
    _, last_day = monthrange(today.year, today.month)

    daily_records = DailyTimeRecord.objects.filter(
        internship=internship, date__month=today.month, date__year=today.year
    )

    # Map records by day number
    records_map = {record.date.day: record for record in daily_records}

    rows = []

    for day in range(1, last_day + 1):
        record = records_map.get(day)

        rows.append(
            {
                "day": day,
                "am_in": record.am_in if record else None,
                "am_out": record.am_out if record else None,
                "pm_in": record.pm_in if record else None,
                "pm_out": record.pm_out if record else None,
                "hours": record.total_hours if record else None,
                "is_holiday": record.is_holiday if record else False,
                "is_weekend": record.is_weekend if record else False,
            }
        )

    return rows


# -----------------------------
# 4️⃣ Main View
# -----------------------------
@login_required
def index(request):
    internship = get_object_or_404(Internship, user=request.user)

    stats = get_internship_stats(internship)
    month_data = get_current_month_data()
    daily_rows = get_daily_rows(internship, month_data["today"])

    context = {
        "internship": internship,
        **stats,
        **month_data,
        "daily_rows": daily_rows,
    }

    return render(request, "pages/index.html", context)


@login_required
def update_daily_record(request):
    if request.method == "POST":
        # Get the internship for the logged-in user
        internship = get_object_or_404(Internship, user=request.user)

        # Get submitted form data
        day = int(request.POST.get("day"))
        am_in = request.POST.get("am_in") or None
        am_out = request.POST.get("am_out") or None
        pm_in = request.POST.get("pm_in") or None
        pm_out = request.POST.get("pm_out") or None

        # Build the date for the record
        today = date.today()
        record_date = today.replace(day=day)

        # Update existing record or create a new one
        DailyTimeRecord.objects.update_or_create(
            internship=internship,
            date=record_date,
            defaults={
                "am_in": am_in,
                "am_out": am_out,
                "pm_in": pm_in,
                "pm_out": pm_out,
            },
        )

    return redirect("index")


@login_required
def mark_day(request):
    if request.method == "POST":
        internship = get_object_or_404(Internship, user=request.user)
        day = int(request.POST.get("day"))
        mark_type = request.POST.get("mark")

        # Build the date
        today = date.today()
        record_date = today.replace(day=day)

        # Get or create the record
        record, created = DailyTimeRecord.objects.get_or_create(
            internship=internship, date=record_date
        )

        # Update holiday or weekend
        if mark_type == "holiday":
            record.is_holiday = True
        elif mark_type == "weekend":
            record.is_weekend = True

        # Recalculate total_hours if necessary
        record.save()

    return redirect("index")


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
