from rest_framework import serializers
from .models import Habit
from django.core.exceptions import ValidationError


class HabitSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания, обновления и вывода привычек.
    """

    description = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Habit
        fields = [
            "id",
            "user",
            "action",
            "location",
            "time",
            "estimated_duration_seconds",
            "periodicity_days",
            "reward_description",
            "is_pleasant",
            "pleasant_habit",
            "is_public",
            "created_at",
            "updated_at",
            "description",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]

        validators = []

    def get_description(self, obj) -> str:
        """Возвращает привычку в формате предложения."""
        return obj.get_full_description()

    def validate_estimated_duration_seconds(self, value):
        if value > 120:
            raise serializers.ValidationError("Время выполнения не может превышать 120 секунд.")
        return value

    def validate_periodicity_days(self, value):
        if not 1 <= value <= 7:
            raise serializers.ValidationError("Периодичность должна быть от 1 до 7 дней.")
        return value

    def validate(self, attrs):
        errors = {}

        # Правило 1: Исключить одновременный выбор текстового вознаграждения и связанной привычки
        if attrs.get("reward_description") and attrs.get("pleasant_habit"):
            errors["reward_description"] = ValidationError(
                "Выберите либо текстовое вознаграждение, либо приятную привычку."
            )
            errors["pleasant_habit"] = ValidationError("Поле недоступно, если указано текстовое вознаграждение.")

        # Правило 2: У новой приятной привычки не может быть награды (при создании)
        if attrs.get("is_pleasant") and self.instance is None:  # Только для создания!
            if attrs.get("reward_description") or attrs.get("pleasant_habit"):
                errors["is_pleasant"] = ValidationError(
                    "У приятной привычки не может быть своего вознаграждения при создании."
                )

        if errors:
            raise serializers.ValidationError(errors)

        return attrs
