from django.core.exceptions import ValidationError


def validate_habit_business_logic(instance):
    """
    Централизованный валидатор бизнес-логики для модели Habit.
    """
    errors = {}

    # Правило 1: Исключить одновременный выбор текстового вознаграждения и связанной привычки
    if instance.reward_description and instance.pleasant_habit_id:
        errors["reward_description"] = ValidationError(
            "Выберите либо текстовое вознаграждение, либо приятную привычку-награду."
        )
        errors["pleasant_habit"] = ValidationError(
            'Поле "Приятная привычка" недоступно, если указано текстовое вознаграждение.'
        )

    # Правило 2: Время выполнения не более 120 секунд
    if instance.estimated_duration_seconds > 120:
        errors["estimated_duration_seconds"] = ValidationError("Время выполнения не может превышать 120 секунд.")

    # Правило 3: Периодичность от 1 до 7 дней
    if not 1 <= instance.periodicity_days <= 7:
        errors["periodicity_days"] = ValidationError(
            "Периодичность должна быть от 1 до 7 дней. Выполняйте привычку хотя бы раз в неделю."
        )

    # Правило 4: У приятной привычки не может быть своего вознаграждения
    if instance.is_pleasant:
        if instance.reward_description or instance.pleasant_habit_id:
            errors["is_pleasant"] = ValidationError(
                "У приятной привычки не может быть собственного вознаграждения или связанных привычек."
            )

    # Правило 5: Связанная привычка должна быть приятной
    if instance.pleasant_habit_id:
        habit_obj = getattr(instance, "_pleasant_habit_cache", None)
        if habit_obj is not None and not habit_obj.is_pleasant:
            errors["pleasant_habit"] = ValidationError(
                'Связанная привычка имеет неверный тип. Выберите привычку с признаком "приятная".'
            )

    if errors:
        raise ValidationError(errors)
