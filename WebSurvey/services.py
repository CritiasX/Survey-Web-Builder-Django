from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import Survey


def auto_close_due_surveys():
    """Mark published surveys as closed once their due date has passed."""
    now = timezone.now()
    overdue_ids = []
    for survey in Survey.objects.filter(status='published', due_date__isnull=False):
        due = survey.due_date
        if due is None:
            continue
        if timezone.is_naive(due):
            due = timezone.make_aware(due, timezone.get_current_timezone())
        if due <= now:
            overdue_ids.append(survey.id)

    if overdue_ids:
        Survey.objects.filter(id__in=overdue_ids).update(status='closed')

    return now


def parse_due_date(value):
    """Convert datetime-local strings into aware datetimes."""
    if not value:
        return None
    dt = parse_datetime(value)
    if not dt:
        return None
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt
