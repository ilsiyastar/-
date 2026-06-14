import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot
from config import TELEGRAM_TOKEN, OWNER_CHAT_ID
from sheets import get_current_streak, get_week_summary, has_habits_today
from claude_client import generate_sales_task
from state import user_state

logger = logging.getLogger(__name__)


async def morning_reminder():
    bot = Bot(token=TELEGRAM_TOKEN)
    streak = get_current_streak()
    text = (
        f"Доброе утро ☀️\n"
        f"🔥 Стрик: {streak} дней\n\n"
        f"Отметь привычки — голосом или текстом"
    )
    await bot.send_message(chat_id=OWNER_CHAT_ID, text=text)
    logger.info("Отправлено утреннее напоминание")


async def evening_reminder():
    if not has_habits_today():
        bot = Bot(token=TELEGRAM_TOKEN)
        await bot.send_message(
            chat_id=OWNER_CHAT_ID,
            text="Яна, не забудь отметить привычки 👆"
        )
        logger.info("Отправлено вечернее напоминание")


async def sales_task_reminder():
    bot = Bot(token=TELEGRAM_TOKEN)
    task = generate_sales_task()
    user_state["waiting_for_sales_answer"] = True
    user_state["current_task"] = task
    await bot.send_message(chat_id=OWNER_CHAT_ID, text=task)
    logger.info("Отправлена задача по продажам")


def setup_scheduler(app):
    scheduler = AsyncIOScheduler(timezone="Asia/Dubai")

    # 08:00 Дубай — утреннее напоминание
    scheduler.add_job(
        morning_reminder,
        CronTrigger(hour=8, minute=0, timezone="Asia/Dubai")
    )

    # 21:00 Дубай — вечернее напоминание (если не отмечено)
    scheduler.add_job(
        evening_reminder,
        CronTrigger(hour=21, minute=0, timezone="Asia/Dubai")
    )

    # Пн, Ср, Пт в 10:00 — задача по продажам
    scheduler.add_job(
        sales_task_reminder,
        CronTrigger(day_of_week="mon,wed,fri", hour=10, minute=0, timezone="Asia/Dubai")
    )

    scheduler.start()
    logger.info("Планировщик запущен")
    return scheduler
