from django.contrib import admin
from .models import Internship, DailyTimeRecord


class DailyTimeRecordInline(admin.TabularInline):  # or StackedInline
    model = DailyTimeRecord
    extra = 0  # how many empty forms to show
    fields = (
        "date",
        "am_in",
        "am_out",
        "pm_in",
        "pm_out",
        "total_hours",
        "is_weekend",
        "is_holiday",
    )
    readonly_fields = ("total_hours",)


@admin.register(Internship)
class InternshipAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "company_name",
        "supervisor_name",
        "start_date",
        "total_hours_required",
        "total_hours_logged",
    )
    search_fields = ("user__username", "company_name", "supervisor_name")
    list_filter = ("start_date",)

    inlines = [DailyTimeRecordInline]  # 👈 THIS is the key part
