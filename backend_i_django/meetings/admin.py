from django.contrib import admin
from django.http import HttpRequest

from .models import ActionItem, Meeting


@admin.action(description="Mark selected action items as done")
def mark_as_completed(modeladmin, request: HttpRequest, queryset) -> None:
    queryset.update(status=ActionItem.STATUS_DONE)


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "date", "owner")
    list_filter = ("date", "owner")
    search_fields = ("title", "owner")


@admin.register(ActionItem)
class ActionItemAdmin(admin.ModelAdmin):
    list_display = ("id", "meeting", "description", "owner", "due_date", "status")
    list_filter = ("status", "due_date")
    search_fields = ("description", "owner")
    actions = [mark_as_completed]
