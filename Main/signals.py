from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import DailyTimeRecord, Internship
from django.db.models import Sum


def recalc_internship_hours(internship):
    total = (
        DailyTimeRecord.objects.filter(internship=internship)
        .aggregate(total=Sum("total_hours"))["total"]
        or 0
    )
    internship.total_hours_logged = total
    internship.save(update_fields=["total_hours_logged"])


@receiver(post_save, sender=DailyTimeRecord)
def update_internship_hours(sender, instance, **kwargs):
    recalc_internship_hours(instance.internship)


@receiver(post_delete, sender=DailyTimeRecord)
def subtract_deleted_hours(sender, instance, **kwargs):
    recalc_internship_hours(instance.internship)