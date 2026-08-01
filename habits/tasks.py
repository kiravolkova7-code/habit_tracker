import logging
import os
from django.utils import timezone
from telegram import Bot
from telegram.error import TelegramError
from dotenv import load_dotenv
from celery import shared_task

from users.models import User
from .models import Habit

load_dotenv()

logger = logging.getLogger(__name__)


@shared_task
def send_bulk_habit_reminders():
    """
    Одна общая задача, которая собирает все напоминания на СЕГОДНЯШНИЙ день
    и рассылает их пользователям.
    """
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        logger.error("Telegram bot token is not configured.")
        return

    today = timezone.localdate()

    active_users = User.objects.filter(telegram_chat_id__isnull=False, is_active=True).only("id", "telegram_chat_id")

    user_ids = list(active_users.values_list("id", flat=True))

    todays_habits = Habit.objects.filter(user_id__in=user_ids, time__isnull=False)

    reminders_to_send = []
    for habit in todays_habits:
        days_since_creation = (today - habit.created_at.date()).days

        if days_since_creation >= habit.periodicity_days and days_since_creation % habit.periodicity_days == 0:
            reminders_to_send.append(habit)

    if not reminders_to_send:
        logger.info("No habits to remind today.")
        return

    bot = Bot(token=bot_token)

    for habit in reminders_to_send:
        try:
            message_text = f"🔔 Напоминание!\n\n" f"{habit.get_full_description()}.\n\n" f"Пора выполнить задачу."

            bot.send_message(chat_id=habit.user.telegram_chat_id, text=message_text)
            logger.info(f"Sent reminder for habit {habit.id} to user {habit.user_id}")

        except TelegramError as e:
            if e.message and ("blocked by the user" in e.message or "chat not found" in e.message):
                habit.user.telegram_chat_id = None
                habit.user.save(update_fields=["telegram_chat_id"])
                logger.warning(f"User {habit.user_id} blocked the bot or deleted chat.")
            else:
                logger.error(f"Telegram API error for habit {habit.id}: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error sending reminder for habit {habit.id}")
