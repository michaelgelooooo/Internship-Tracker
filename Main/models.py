from django.db import models
from django.contrib.auth.models import User

class Internship(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=200)
    start_date = models.DateField()
    total_hours_required = models.FloatField(help_text="Total hours required for internship")
    total_hours_logged = models.FloatField(default=0, help_text="Total hours recorded so far")
    supervisor_name = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.user.username} @ {self.company_name}"


class DailyTimeRecord(models.Model):
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE)
    date = models.DateField()
    am_in = models.TimeField(null=True, blank=True)
    am_out = models.TimeField(null=True, blank=True)
    pm_in = models.TimeField(null=True, blank=True)
    pm_out = models.TimeField(null=True, blank=True)
    total_hours = models.FloatField(default=0, help_text="Total hours worked this day")

    class Meta:
        unique_together = ('internship', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.internship.user.username} - {self.date}"