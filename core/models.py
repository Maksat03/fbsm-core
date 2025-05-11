from django.db import models


IDEMPOTENCY_STATUSES = (
    ("applied", "Applied"),
    ("rolled-back", "Rolled Back")
)


class Idempotency(models.Model):
    status = models.CharField(max_length=30, choices=IDEMPOTENCY_STATUSES, default="applied")

    path = models.CharField(max_length=500)
    key = models.CharField(max_length=500)

    request = models.JSONField(null=True)
    response = models.JSONField(null=True)
    help_data = models.JSONField(null=True)
