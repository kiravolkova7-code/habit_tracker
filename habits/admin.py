from django.contrib import admin
from .models import Habit


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    """
    Админка для привычек.
    """

    list_display = (
        "id",
        "get_full_description",
        "user",
        "is_public",
        "is_pleasant",
        "periodicity_days",
        "estimated_duration_seconds",
        "created_at",
    )

    list_filter = ("is_public", "is_pleasant", "user", "periodicity_days", "created_at")

    search_fields = (
        "action",
        "location",
        "time",
    )

    readonly_fields = ("user", "created_at", "updated_at")

    raw_id_fields = ("pleasant_habit",)

    autocomplete_fields = ()

    ordering = ("-created_at", "-updated_at")

    fieldsets = (
        (None, {"fields": ("user", "action", "location", "time")}),
        ("Параметры выполнения", {"fields": ("estimated_duration_seconds", "periodicity_days")}),
        ("Связи и вознаграждения", {"fields": ("reward_description", "is_pleasant", "pleasant_habit")}),
        ("Публичность", {"fields": ("is_public",)}),
        (
            "Служебные данные",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request):
        """
        Администратор видит только свои привычки
        и публичные привычки других пользователей.
        """
        qs = super().get_queryset(request)
        return qs.filter(user=request.user) | qs.filter(is_public=True)

    def save_model(self, request, obj, form, change):
        """
        Этот метод вызывается при сохранении объекта в админке.
        """
        if not change:
            obj.user = request.user

        super().save_model(request, obj, form, change)
