import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot
from config import TELEGRAM_TOKEN, OWNER_CHAT_ID
from sheets import get_current_streak, has_habits_today
from claude_client import generate_sales_task
from state import user_state

logger = logging.getLogger(__name__)


async def morning_reminder():
    bot = Bot(token=TELEGRAM_TOKEN)
    streak = get_current_streak()

    if streak == 0:
        streak_text = "Начни стрик сегодня 💪"
    elif streak == 1:
        streak_text = "🔥 Стрик: 1 день — хорошее начало!"
    elif streak < 7:
        streak_text = f"🔥 Стрик: {streak} дня — продолжай!"
    elif streak < 14:
        streak_text = f"🔥 Стрик: {streak} дней — ты в потоке!"
    else:
        streak_text = f"🔥 Стрик: {streak} дней — огонь, не останавливайся!"

    text = (
        f"Доброе утро ☀️\n\n"
        f"{streak_text}\n\n"
        f"Сегодня твои 5 привычек:\n"
        f"🚶 10 000 шагов\n"
        f"🧘 Медитация\n"
        f"🕉 Йога\n"
        f"🇬🇧 Английский\n"
        f"📚 Чтение\n\n"
        f"Отметь голосом или текстом что сделала 👇"
    )
    await bot.send_message(chat_id=OWNER_CHAT_ID, text=text)
    logger.info("Отправлено утреннее напоминание")


async def evening_reminder():
    if not has_habits_today():
        bot = Bot(token=TELEGRAM_TOKEN)
        await bot.send_message(
            chat_id=OWNER_CHAT_ID,
            text="Яна, день ещё не закрыт 👆\nОтметь привычки — даже если сделала не всё, это считается."
        )
        logger.info("Отправлено вечернее напоминание")


async def sales_task_reminder():
    bot = Bot(token=TELEGRAM_TOKEN)
    task = generate_sales_task()
    user_state["waiting_for_sales_answer"] = True
    user_state["current_task"] = task
    await bot.send_message(chat_id=OWNER_CHAT_ID, text=f"💼 Задача по продажам:\n\n{task}")
    logger.info("Отправлена задача по продажам")


def setup_scheduler(app):
    scheduler = AsyncIOScheduler(timezone="Asia/Dubai")

    scheduler.add_job(
        morning_reminder,
        CronTrigger(hour=8, minute=0, timezone="Asia/Dubai")
    )

    scheduler.add_job(
        evening_reminder,
        CronTrigger(hour=21, minute=0, timezone="Asia/Dubai")
    )

    scheduler.add_job(
        sales_task_reminder,
        CronTrigger(day_of_week="mon,wed,fri", hour=10, minute=0, timezone="Asia/Dubai")
    )

    scheduler.start()
    logger.info("Планировщик запущен")
    return scheduler
