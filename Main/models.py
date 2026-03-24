from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.db.models import Sum
from django.core.exceptions import ValidationError


class Internship(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=200)
    start_date = models.DateField()
    total_hours_required = models.FloatField(
        help_text="Total hours required for internship"
    )
    supervisor_name = models.CharField(max_length=100, blank=True)

    @property
    def total_hours_logged(self):
        result = self.dailytimerecord_set.aggregate(total=Sum("total_hours"))
        return result["total"] or 0.0

    def __str__(self):
        return f"{self.user.username} @ {self.company_name}"


class DailyTimeRecord(models.Model):
    internship = models.ForeignKey("Internship", on_delete=models.CASCADE)
    date = models.DateField()

    am_in = models.TimeField(null=True, blank=True)
    am_out = models.TimeField(null=True, blank=True)
    pm_in = models.TimeField(null=True, blank=True)
    pm_out = models.TimeField(null=True, blank=True)

    total_hours = models.FloatField(default=0)
    is_holiday = models.BooleanField(default=False)
    is_weekend = models.BooleanField(default=False)

    class Meta:
        unique_together = ("internship", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.internship.user.username} - {self.date}"

    def round_up_30(self, t):
        if not t:
            return None

        dt = datetime.combine(self.date, t)

        remainder = dt.minute % 30
        if remainder != 0:
            dt += timedelta(minutes=(30 - remainder))

        # zero out seconds
        dt = dt.replace(second=0, microsecond=0)

        return dt.time()

    def round_down_30(self, t):
        if not t:
            return None

        dt = datetime.combine(self.date, t)

        remainder = dt.minute % 30
        dt -= timedelta(minutes=remainder)

        # zero out seconds
        dt = dt.replace(second=0, microsecond=0)

        return dt.time()

    def calculate_block(self, time_in, time_out):
        # If either is missing, block is incomplete → return 0
        if not time_in or not time_out:
            return 0

        # Round times
        time_in = self.round_up_30(time_in)
        time_out = self.round_down_30(time_out)

        # If after rounding, block is invalid → 0
        if time_out <= time_in:
            return 0

        dt_in = datetime.combine(self.date, time_in)
        dt_out = datetime.combine(self.date, time_out)
        diff = dt_out - dt_in
        return diff.total_seconds() / 3600

    def clean(self):
        errors = {}

        if self.am_in and self.am_out and self.am_out <= self.am_in:
            errors["am_out"] = "AM out must be after AM in."

        if self.pm_in and self.pm_out and self.pm_out <= self.pm_in:
            errors["pm_out"] = "PM out must be after PM in."

        if self.am_out and self.pm_in and self.pm_in <= self.am_out:
            errors["pm_in"] = "PM in must be after AM out."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()

        if self.is_weekend or self.is_holiday:
            self.total_hours = 0
        else:
            am_hours = self.calculate_block(self.am_in, self.am_out)
            pm_hours = self.calculate_block(self.pm_in, self.pm_out)
            self.total_hours = am_hours + pm_hours

        super().save(*args, **kwargs)
