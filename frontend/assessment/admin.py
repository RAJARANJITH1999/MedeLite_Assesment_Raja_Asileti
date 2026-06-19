from django.contrib import admin

from assessment.models import SavedLookup


@admin.register(SavedLookup)
class SavedLookupAdmin(admin.ModelAdmin):
    list_display = ("facility_name", "ccn", "state", "overall_rating", "looked_up_at")
    search_fields = ("facility_name", "ccn")
    list_filter = ("state",)
