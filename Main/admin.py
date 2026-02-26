from django.contrib import admin
from .models import Internship, DailyTimeRecord


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


@admin.register(DailyTimeRecord)
class DailyTimeRecordAdmin(admin.ModelAdmin):
    list_display = (
        "internship",
        "date",
        "am_in",
        "am_out",
        "pm_in",
        "pm_out",
        "total_hours",
    )
    search_fields = ("internship__user__username", "internship__company_name")
    list_filter = ("date",)
