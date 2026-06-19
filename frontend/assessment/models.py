from django.db import models


class SavedLookup(models.Model):
    """A snapshot of one CCN lookup + manual inputs, kept for history/comparison."""

    ccn = models.CharField(max_length=6)
    facility_name = models.CharField(max_length=255)
    state = models.CharField(max_length=2)
    overall_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    looked_up_at = models.DateTimeField(auto_now_add=True)

    facility_data = models.JSONField()
    manual_inputs = models.JSONField()
    ai_summary = models.TextField(blank=True, default="")
    ai_summary_generated_by = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        ordering = ["-looked_up_at"]

    def __str__(self) -> str:
        return f"{self.facility_name} ({self.ccn}) @ {self.looked_up_at:%Y-%m-%d %H:%M}"
