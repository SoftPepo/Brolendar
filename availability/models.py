from django.conf import settings
from django.db.models import (
    CharField,
    CheckConstraint,
    DateTimeField,
    F,
    ForeignKey,
    Index,
    Model,
    Q,
)
from django.db.models.deletion import CASCADE, SET_NULL
from django.db.models.enums import TextChoices
from django.db.models.fields.composite import CompositePrimaryKey


class CalendarColor(TextChoices):
    RED = "red", "Red"
    BLUE = "blue", "Blue"
    GREEN = "green", "Green"


class BusyBlock(Model):
    group = ForeignKey("groups.Group", on_delete=CASCADE, related_name="blocks")
    user = ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name="blocks")
    name = CharField(max_length=30)
    starts_at = DateTimeField()
    ends_at = DateTimeField()
    color = CharField(max_length=20, choices=CalendarColor, default=CalendarColor.BLUE)
    note = CharField(max_length=100, blank=True, null=True)
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            CheckConstraint(
                condition=Q(ends_at__gt=F("starts_at")),
                name="busyblock_ends_after_starts",
            )
        ]


class Event(Model):
    class EventStatus(TextChoices):
        ACTIVE = "active", "Active"
        CANCELED = "canceled", "Canceled"

    group = ForeignKey("groups.Group", on_delete=CASCADE, related_name="events")
    creator = ForeignKey(settings.AUTH_USER_MODEL, on_delete=SET_NULL, related_name="created_events", null=True)
    name = CharField(max_length=30)
    status = CharField(max_length=20, choices=EventStatus, default=EventStatus.ACTIVE)
    starts_at = DateTimeField()
    ends_at = DateTimeField()
    color = CharField(max_length=20, choices=CalendarColor, default=CalendarColor.BLUE)
    note = CharField(max_length=100, blank=True, null=True)
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            CheckConstraint(
                condition=Q(ends_at__gt=F("starts_at")),
                name="event_ends_after_starts",
            )
        ]


class EventResponse(Model):
    class ResponseStatus(TextChoices):
        YES = "yes", "Yes"
        MAYBE = "maybe", "Maybe"
        NO = "no", "No"

    pk = CompositePrimaryKey("event_id", "user_id")
    user = ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name="event_responses")
    event = ForeignKey(Event, on_delete=CASCADE, related_name="responses")
    status = CharField(max_length=20, choices=ResponseStatus)
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [Index(fields=["user"])]
