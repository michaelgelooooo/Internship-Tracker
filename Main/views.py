from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Sum
from django.contrib import messages
from datetime import datetime, date, timedelta
from django.utils import timezone
from calendar import monthrange
from .models import Internship, DailyTimeRecord
from django.core.exceptions import ValidationError
from django.http import JsonResponse
import math


def get_internship_stats(internship):
    today = date.today()

    # --- Overall ---
    total_logged = internship.total_hours_logged
    total_required = internship.total_hours_required
    remaining_hours = max(total_required - total_logged, 0)
    percent_complete = (total_logged / total_required) * 100 if total_required else 0

    total_days_logged = (
        DailyTimeRecord.objects.filter(
            internship=internship, is_holiday=False, is_weekend=False
        )
        .filter(
            Q(am_in__isnull=False, am_out__isnull=False)
            | Q(pm_in__isnull=False, pm_out__isnull=False)
        )
        .count()
    )

    # Fetch all holiday dates once — reused across calculations
    holiday_dates = set(
        DailyTimeRecord.objects.filter(
            internship=internship,
            is_holiday=True,
        ).values_list("date", flat=True)
    )

    def is_working_day(d):
        return d.weekday() < 4 and d not in holiday_dates

    def add_workdays(start_date, workdays):
        current_date = start_date
        days_added = 0
        while days_added < workdays:
            current_date += timedelta(days=1)
            if is_working_day(current_date):
                days_added += 1
        return current_date

    standard_hours_per_week = 40
    standard_hours_per_day = 10

    if remaining_hours > 0:
        days_left = int((remaining_hours / standard_hours_per_day) + 0.999)
        projected_completion = add_workdays(today, days_left)
    else:
        days_left = 0
        projected_completion = today

    # --- Pace ---
    total_avg = round(total_logged / max(total_days_logged, 1), 2)
    weeks_left = math.ceil(days_left / 4) if days_left > 0 else 0

    start_date = internship.start_date

    # Count actual working days elapsed since start excluding holidays and today
    workdays_elapsed = sum(
        1
        for i in range((today - start_date).days)  # stops before today
        if is_working_day(start_date + timedelta(days=i))
    )
    weeks_elapsed = workdays_elapsed / 4
    expected_hours_by_now = round(weeks_elapsed * standard_hours_per_week, 2)
    hours_ahead_behind = round(total_logged - expected_hours_by_now, 2)

    if hours_ahead_behind > 0:
        pace_status = "Ahead"
    elif hours_ahead_behind < 0:
        pace_status = "Behind"
    else:
        pace_status = "On Track"

    required_avg_going_forward = (
        round(remaining_hours / weeks_left, 2) if weeks_left > 0 else 0
    )

    # --- Monthly ---
    monthly_records = DailyTimeRecord.objects.filter(
        internship=internship,
        date__year=today.year,
        date__month=today.month,
        is_holiday=False,
        is_weekend=False,
    )

    hours_this_month = monthly_records.aggregate(total=Sum("total_hours"))["total"] or 0

    days_attended_this_month = monthly_records.filter(
        Q(am_in__isnull=False, am_out__isnull=False)
        | Q(pm_in__isnull=False, pm_out__isnull=False)
    ).count()

    monthly_avg = round(hours_this_month / max(days_attended_this_month, 1), 2)

    _, last_day = monthrange(today.year, today.month)

    # Workdays elapsed this month excluding holidays and today
    workdays_elapsed_this_month = sum(
        1
        for d in range(1, today.day)  # exclude today
        if is_working_day(date(today.year, today.month, d))
    )

    # Workdays remaining this month excluding holidays (starts from tomorrow)
    workdays_remaining_in_month = sum(
        1
        for d in range(today.day + 1, last_day + 1)
        if is_working_day(date(today.year, today.month, d))
    )

    # Monthly hours based on 40hr work week
    total_workdays_this_month = (
        workdays_elapsed_this_month + workdays_remaining_in_month
    )
    weeks_in_month = total_workdays_this_month / 4
    hours_required_this_month = round(weeks_in_month * standard_hours_per_week, 2)
    hours_remaining_this_month = round(
        max(hours_required_this_month - hours_this_month, 0), 2
    )
    percent_complete_this_month = round(
        (
            (hours_this_month / hours_required_this_month) * 100
            if hours_required_this_month
            else 0
        ),
        1,
    )
    projected_hours_end_of_month = round(
        hours_this_month + (monthly_avg * workdays_remaining_in_month), 2
    )

    return {
        # Overall
        "total_logged": total_logged,
        "total_required": total_required,
        "remaining_hours": remaining_hours,
        "percent_complete": percent_complete,
        "total_days_logged": total_days_logged,
        "projected_completion": projected_completion,
        # Pace
        "total_avg": total_avg,
        "days_left": days_left,
        "weeks_left": weeks_left,
        "expected_hours_by_now": expected_hours_by_now,
        "hours_ahead_behind": hours_ahead_behind,
        "pace_status": pace_status,
        "required_avg_going_forward": required_avg_going_forward,
        # Monthly
        "hours_this_month": hours_this_month,
        "hours_required_this_month": hours_required_this_month,
        "hours_remaining_this_month": hours_remaining_this_month,
        "percent_complete_this_month": percent_complete_this_month,
        "days_attended_this_month": days_attended_this_month,
        "workdays_remaining_in_month": workdays_remaining_in_month,
        "projected_hours_end_of_month": projected_hours_end_of_month,
    }


def build_months_rows(records_map, year):
    """
    Returns list of months with daily records for template rendering
    """
    months_rows = []
    for month_num in range(1, 13):
        _, last_day = monthrange(year, month_num)
        rows = []
        for day in range(1, last_day + 1):
            record = records_map.get((month_num, day))
            rows.append(
                {
                    "day": day,
                    "month_num": month_num,
                    "year": year,
                    "am_in": record.am_in if record else None,
                    "am_out": record.am_out if record else None,
                    "pm_in": record.pm_in if record else None,
                    "pm_out": record.pm_out if record else None,
                    "hours": record.total_hours if record else None,
                    "is_holiday": record.is_holiday if record else False,
                    "is_weekend": record.is_weekend if record else False,
                    "is_absent": record.is_absent if record else False,  # ADD THIS
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
    return months_rows


def get_daily_records(internship, year):
    daily_records = DailyTimeRecord.objects.filter(
        internship=internship, date__year=year
    )
    return {(r.date.month, r.date.day): r for r in daily_records}


@login_required
def get_daily_record(request):
    try:
        day = int(request.GET.get("day"))
        month = int(request.GET.get("month"))
        year = int(request.GET.get("year"))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid date"}, status=400)

    internship = get_object_or_404(Internship, user=request.user)
    record_date = date(year, month, day)
    record = DailyTimeRecord.objects.filter(
        internship=internship, date=record_date
    ).first()

    return JsonResponse(
        {
            "day": day,
            "month": month,
            "year": year,
            "am_in": record.am_in.strftime("%H:%M") if record and record.am_in else "",
            "am_out": (
                record.am_out.strftime("%H:%M") if record and record.am_out else ""
            ),
            "pm_in": record.pm_in.strftime("%H:%M") if record and record.pm_in else "",
            "pm_out": (
                record.pm_out.strftime("%H:%M") if record and record.pm_out else ""
            ),
            "is_holiday": record.is_holiday if record else False,
            "is_weekend": record.is_weekend if record else False,
            "is_absent": record.is_absent if record else False,  # ADD THIS
        }
    )


def get_next_quick_log_action(internship, today_record=None):
    if today_record is None:
        today_record = DailyTimeRecord.objects.filter(
            internship=internship, date=timezone.localdate()
        ).first()

    if not today_record:
        return "am_in"

    if (
        today_record.is_holiday or today_record.is_weekend or today_record.is_absent
    ):  # ADD is_absent
        return None

    if not today_record.am_in:
        return "am_in"
    if not today_record.am_out:
        return "am_out"
    if not today_record.pm_in:
        return "pm_in"
    if not today_record.pm_out:
        return "pm_out"

    return None


ACTION_LABELS = {
    "am_in": "Time In (AM)",
    "am_out": "Time Out (AM)",
    "pm_in": "Time In (PM)",
    "pm_out": "Time Out (PM)",
}


@login_required
def mark_day(request):
    if request.method == "POST":
        try:
            day = int(request.POST.get("day"))
            month = int(request.POST.get("month"))
            year = int(request.POST.get("year"))
        except (TypeError, ValueError):
            return redirect("index")

        internship = get_object_or_404(Internship, user=request.user)
        mark_type = request.POST.get("mark")
        record_date = date(year, month, day)

        record, created = DailyTimeRecord.objects.get_or_create(
            internship=internship, date=record_date
        )

        if mark_type == "holiday":
            if record.is_holiday:
                # Unmarking - delete if no time entries exist
                if not any([record.am_in, record.am_out, record.pm_in, record.pm_out]):
                    record.delete()
                else:
                    record.is_holiday = False
                    record.save()
                redirect_month = request.POST.get("redirect_month", month)
                redirect_year = request.POST.get("redirect_year", year)
                return redirect(
                    f"{reverse('index')}?month={redirect_month}&year={redirect_year}"
                )
            else:
                record.is_holiday = True
                record.is_weekend = False
                record.is_absent = False
                record.am_in = None
                record.am_out = None
                record.pm_in = None
                record.pm_out = None

        elif mark_type == "weekend":
            if record.is_weekend:
                # Unmarking - delete if no time entries exist
                if not any([record.am_in, record.am_out, record.pm_in, record.pm_out]):
                    record.delete()
                else:
                    record.is_weekend = False
                    record.save()
                redirect_month = request.POST.get("redirect_month", month)
                redirect_year = request.POST.get("redirect_year", year)
                return redirect(
                    f"{reverse('index')}?month={redirect_month}&year={redirect_year}"
                )
            else:
                record.is_weekend = True
                record.is_holiday = False
                record.is_absent = False
                record.am_in = None
                record.am_out = None
                record.pm_in = None
                record.pm_out = None

        elif mark_type == "absent":
            if record.is_absent:
                # Unmarking - delete if no time entries exist
                if not any([record.am_in, record.am_out, record.pm_in, record.pm_out]):
                    record.delete()
                else:
                    record.is_absent = False
                    record.save()
                redirect_month = request.POST.get("redirect_month", month)
                redirect_year = request.POST.get("redirect_year", year)
                return redirect(
                    f"{reverse('index')}?month={redirect_month}&year={redirect_year}"
                )
            else:
                record.is_absent = True
                record.is_holiday = False
                record.is_weekend = False
                record.am_in = None
                record.am_out = None
                record.pm_in = None
                record.pm_out = None

        try:
            record.save()
        except ValidationError:
            messages.error(
                request, "Could not mark day due to existing invalid time entries."
            )

        redirect_month = request.POST.get("redirect_month", month)
        redirect_year = request.POST.get("redirect_year", year)

        return redirect(
            f"{reverse('index')}?month={redirect_month}&year={redirect_year}"
        )

    return redirect("index")


@login_required
def update_daily_record(request):
    if request.method == "POST":
        try:
            day = int(request.POST.get("day"))
            month = int(request.POST.get("month"))
            year = int(request.POST.get("year"))
        except (TypeError, ValueError):
            return redirect("index")

        internship = get_object_or_404(Internship, user=request.user)

        def str_to_time(s):
            if not s:
                return None
            return datetime.strptime(s.strip(), "%H:%M").time()

        am_in = str_to_time(request.POST.get("am_in"))
        am_out = str_to_time(request.POST.get("am_out"))
        pm_in = str_to_time(request.POST.get("pm_in"))
        pm_out = str_to_time(request.POST.get("pm_out"))

        record_date = date(year, month, day)
        all_empty = all(f is None for f in [am_in, am_out, pm_in, pm_out])

        record = DailyTimeRecord.objects.filter(
            internship=internship, date=record_date
        ).first()

        if all_empty:
            if record and not record.is_weekend and not record.is_holiday:
                record.delete()
        else:
            if not record:
                record = DailyTimeRecord(internship=internship, date=record_date)
            record.am_in = am_in
            record.am_out = am_out
            record.pm_in = pm_in
            record.pm_out = pm_out
            try:
                record.save()
            except ValidationError:
                messages.error(
                    request, "Invalid time entries. Please check the time order."
                )

        return redirect(f"{reverse('index')}?month={month}&year={year}")

    return redirect("index")


@login_required
def delete_daily_record(request):
    if request.method == "POST":
        try:
            day = int(request.POST.get("day"))
            month = int(request.POST.get("month"))
            year = int(request.POST.get("year"))
        except (TypeError, ValueError):
            return redirect("index")

        internship = get_object_or_404(Internship, user=request.user)
        record_date = date(year, month, day)
        record = DailyTimeRecord.objects.filter(
            internship=internship, date=record_date
        ).first()
        if record:
            record.delete()

        return redirect(f"{reverse('index')}?month={month}&year={year}")

    return redirect("index")


@login_required
def quick_log(request):
    if request.method == "POST":
        action = request.POST.get("log_action")
        internship = Internship.objects.get(user=request.user)

        now = timezone.localtime()
        date_obj = now.date()
        time_obj = now.time()

        # Single DB query reused for both checks
        existing = DailyTimeRecord.objects.filter(
            internship=internship, date=date_obj
        ).first()

        expected_action = get_next_quick_log_action(internship, existing)
        if action != expected_action or expected_action is None:
            messages.error(request, "Invalid log action.")
            return redirect("index")

        if existing and (
            existing.is_holiday or existing.is_weekend or existing.is_absent
        ):  # ADD is_absent
            messages.error(
                request, "Cannot log time on a holiday, weekend, or absent day."
            )
            return redirect("index")

        record, created = DailyTimeRecord.objects.get_or_create(
            internship=internship, date=date_obj
        )

        try:
            setattr(record, action, time_obj)
            record.save()
        except ValidationError:
            messages.error(request, "Invalid log action.")

    return redirect("index")


@login_required
def index(request):
    internship = get_object_or_404(Internship, user=request.user)
    stats = get_internship_stats(internship)

    # Current month and year
    current_month = int(request.GET.get("month", date.today().month))
    current_year = int(request.GET.get("year", date.today().year))

    # Prev/Next month with year rollover
    if current_month == 1:
        prev_month = 12
        prev_year = current_year - 1
    else:
        prev_month = current_month - 1
        prev_year = current_year

    if current_month == 12:
        next_month = 1
        next_year = current_year + 1
    else:
        next_month = current_month + 1
        next_year = current_year

    # Build daily records
    records_map = get_daily_records(internship, current_year)
    months_rows = build_months_rows(records_map, current_year)

    today = timezone.localdate()
    today_record = DailyTimeRecord.objects.filter(
        internship=internship, date=today
    ).first()
    next_action = get_next_quick_log_action(internship, today_record)
    next_action_label = ACTION_LABELS.get(next_action, "No more actions for today")

    context = {
        "internship": internship,
        **stats,
        "months_rows": months_rows,
        "current_month": current_month,
        "current_year": current_year,
        "prev_month": prev_month,
        "prev_year": prev_year,
        "next_month": next_month,
        "next_year": next_year,
        "next_action": next_action,
        "next_action_label": next_action_label,
        "today_quick_log": today,
        "today_is_holiday": today_record.is_holiday if today_record else False,
        "today_is_weekend": today_record.is_weekend if today_record else False,
        "today_is_absent": today_record.is_absent if today_record else False,
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
            return redirect(f"{reverse('auth')}?tab=login")

    return redirect("auth")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("index")

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        company_name = request.POST.get("company_name")
        supervisor_name = request.POST.get("supervisor_name")
        start_date = request.POST.get("start_date")
        total_hours_required = request.POST.get("total_hours_required")

        # Validation
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect(f"{reverse('auth')}?tab=register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect(f"{reverse('auth')}?tab=register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect(f"{reverse('auth')}?tab=register")

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
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


@login_required
def update_user_info(request):
    if request.method == "POST":
        user = request.user
        internship = get_object_or_404(Internship, user=user)

        # Get form data
        username = request.POST.get("username").strip()
        email = request.POST.get("email").strip()
        first_name = request.POST.get("first_name").strip()
        last_name = request.POST.get("last_name").strip()
        company_name = request.POST.get("company_name").strip()
        supervisor_name = request.POST.get("supervisor_name").strip()
        start_date = request.POST.get("start_date")
        total_hours_required = request.POST.get("total_hours_required")

        # Validate unique username
        if User.objects.filter(username=username).exclude(pk=user.pk).exists():
            messages.error(request, "Username already exists.")
            return redirect(request.META.get("HTTP_REFERER", "/"))

        # Validate unique email
        if User.objects.filter(email=email).exclude(pk=user.pk).exists():
            messages.error(request, "Email already registered.")
            return redirect(request.META.get("HTTP_REFERER", "/"))

        # Update user fields
        user.username = username
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.save()

        # Update internship fields
        internship.company_name = company_name
        internship.supervisor_name = supervisor_name
        internship.start_date = start_date
        internship.total_hours_required = total_hours_required
        internship.save()

        messages.success(request, "User information updated successfully.")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    # Fallback
    return redirect("index")


def logout_view(request):
    logout(request)

    return redirect("auth")
