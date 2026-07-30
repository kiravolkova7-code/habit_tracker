from django.db import models
from django.conf import settings
from .validators import validate_habit_business_logic


class Habit(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='habits'
    )

    action = models.TextField(
        verbose_name='Действие',
        help_text='Что конкретно нужно сделать?'
    )

    location = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Место',
    )

    time = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Время',
    )

    estimated_duration_seconds = models.PositiveSmallIntegerField(
        default=120,
        verbose_name='Время на выполнение (секунды)',
        help_text='Максимум 120 секунд.'
    )

    periodicity_days = models.PositiveIntegerField(
        default=1,
        verbose_name='Периодичность (в днях)',
        help_text='Через сколько дней повторять напоминание. От 1 до 7.'
    )

    reward_description = models.TextField(
        blank=True,
        verbose_name='Вознаграждение (текстом)',
    )

    is_pleasant = models.BooleanField(
        default=False,
        verbose_name='Признак приятной привычки',
        help_text='Отметьте, если это приятная привычка-награда.'
    )

    pleasant_habit = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='rewarded_for',
        limit_choices_to={'is_pleasant': True},
        verbose_name='Приятная привычка-награда',
    )

    is_public = models.BooleanField(
        default=False,
        verbose_name='Опубликовать в общий доступ',
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    def __str__(self):
        return self.get_full_description()

    def get_full_description(self) -> str:
        parts = ['Я буду', self.action.strip()]
        if self.time:
            parts.append(f'в {self.time.strip()}')
        if self.location:
            parts.append(f'в {self.location.strip()}')
        return ' '.join(parts)

    class Meta:
        verbose_name = 'Привычка'
        verbose_name_plural = 'Привычки'
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(estimated_duration_seconds__lte=120),
                name='duration_max_120_seconds'
            ),
            models.CheckConstraint(
                condition=~models.Q(id=models.F('pleasant_habit_id')),
                name='no_self_reward_loop_db'
            ),
        ]

    def clean(self):
        super().clean()

        validate_habit_business_logic(self)
