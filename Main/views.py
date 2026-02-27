from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from datetime import datetime, date, time
from calendar import monthrange
from .models import Internship, DailyTimeRecord


# -----------------------------
# Internship Statistics
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
# Month Data
# -----------------------------
def get_year_data(year=None):
    if not year:
        year = date.today().year

    year_data = []

    for month in range(1, 13):
        first_day = date(year, month, 1)
        _, last_day = monthrange(year, month)
        days_in_month = list(range(1, last_day + 1))

        year_data.append(
            {
                "month": first_day.strftime("%B"),  # Month name
                "month_num": month,
                "year": year,
                "first_day_of_month": first_day,
                "days_in_month": days_in_month,
            }
        )

    return year_data


# -----------------------------
#  Daily Data
# -----------------------------
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


@login_required
def update_daily_record(request):
    if request.method == "POST":
        internship = get_object_or_404(Internship, user=request.user)
        day = int(request.POST.get("day"))

        # Helper to convert string to time
        def str_to_time(s):
            if not s:
                return None
            return datetime.strptime(s.strip(), "%H:%M").time()

        am_in = str_to_time(request.POST.get("am_in"))
        am_out = str_to_time(request.POST.get("am_out"))
        pm_in = str_to_time(request.POST.get("pm_in"))
        pm_out = str_to_time(request.POST.get("pm_out"))

        record_date = date.today().replace(day=day)

        # ✅ Get or create the DTR
        record, created = DailyTimeRecord.objects.get_or_create(
            internship=internship, date=record_date
        )

        # ✅ Update fields manually
        record.am_in = am_in
        record.am_out = am_out
        record.pm_in = pm_in
        record.pm_out = pm_out

        # ✅ Save triggers save() and post_save signals
        record.save()

    return redirect("index")


@login_required
def index(request):
    internship = get_object_or_404(Internship, user=request.user)
    stats = get_internship_stats(internship)

    # Get current month from query param, default to today
    current_month = request.GET.get("month")
    if current_month:
        current_month = int(current_month)
    else:
        current_month = date.today().month

    year = date.today().year

    # Compute prev/next month for buttons
    prev_month = current_month - 1 if current_month > 1 else 12
    next_month = current_month + 1 if current_month < 12 else 1

    # Get all DTRs for the year
    daily_records = DailyTimeRecord.objects.filter(
        internship=internship, date__year=year
    )
    records_map = {(r.date.month, r.date.day): r for r in daily_records}

    # Build data for all months
    months_rows = []
    for month_num in range(1, 13):
        _, last_day = monthrange(year, month_num)
        rows = []
        for day in range(1, last_day + 1):
            record = records_map.get((month_num, day))
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
        months_rows.append(
            {
                "month": date(year, month_num, 1).strftime("%B"),
                "month_num": month_num,
                "year": year,
                "rows": rows,
            }
        )

    context = {
        "internship": internship,
        **stats,
        "months_rows": months_rows,
        "current_month": current_month,
        "prev_month": prev_month,
        "next_month": next_month,
    }

    return render(request, "pages/index.html", context)


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
