import logging
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from config import TELEGRAM_TOKEN, OWNER_CHAT_ID
from state import user_state
from sheets import get_current_streak, get_best_streak, get_week_summary, save_habits, save_sales
from claude_client import process_habits, process_sales_review, generate_sales_task
from voice import transcribe_voice

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

_lock = asyncio.Lock()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != OWNER_CHAT_ID:
        return
    await update.message.reply_text(
        "Привет! Я твой личный ассистент.\n\n"
        "Отмечай привычки голосом или текстом:\n"
        "'сделала медитацию, прошла 8к шагов'\n\n"
        "Команды:\n"
        "/summary — итог недели\n"
        "/streak — текущий стрик\n"
        "/task — задача по продажам\n"
        "/history — последние 5 заданий"
    )


async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != OWNER_CHAT_ID:
        return
    text = get_week_summary()
    await update.message.reply_text(text)


async def streak(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != OWNER_CHAT_ID:
        return
    current = get_current_streak()
    best = get_best_streak()
    await update.message.reply_text(f"🔥 Текущий стрик: {current} дней\n🏆 Лучший стрик: {best} дней")


async def task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != OWNER_CHAT_ID:
        return
    await _send_sales_task(update)


async def _send_sales_task(update):
    t = generate_sales_task()
    user_state["waiting_for_sales_answer"] = True
    user_state["current_task"] = t
    await update.message.reply_text(t)


async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != OWNER_CHAT_ID:
        return
    from sheets import get_sales_history
    text = get_sales_history()
    await update.message.reply_text(text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != OWNER_CHAT_ID:
        return

    async with _lock:
        if update.message.voice:
            await update.message.reply_text("🎙 Слушаю...")
            text = await transcribe_voice(update.message.voice, context)
            if not text:
                await update.message.reply_text("Не смог распознать голос, попробуй ещё раз")
                return
        else:
            text = update.message.text

        if user_state["waiting_for_sales_answer"]:
            t = user_state["current_task"]
            review = process_sales_review(t, text)
            score = _extract_score(review)
            save_sales(t, text, review, score)
            user_state["waiting_for_sales_answer"] = False
            user_state["current_task"] = None
            await update.message.reply_text(review)
        else:
            result = process_habits(text)
            if result is None:
                await update.message.reply_text("Не понял, попробуй написать иначе 🙏")
                return
            streak_data = save_habits(result)
            response = _format_habits_response(result, streak_data)
            await update.message.reply_text(response)


def _extract_score(review_text: str):
    import re
    match = re.search(r'Оценка:\s*([1-5])/5', review_text)
    if match:
        return int(match.group(1))
    return None


def _format_habits_response(habits: dict, streak_data: dict) -> str:
    lines = ["✅ Зафиксировано:"]
    lines.append(f"🚶 Шаги — {'да' if habits.get('шаги') else 'нет'}")
    lines.append(f"🧘 Медитация — {'да' if habits.get('медитация') else 'нет'}")
    lines.append(f"🕉 Йога — {'да' if habits.get('йога') else 'нет'}")
    lines.append(f"🇬🇧 Английский — {'да' if habits.get('английский') else 'нет'}")
    lines.append(f"📚 Чтение — {'да' if habits.get('чтение') else 'нет'}")
    lines.append("")
    current = streak_data.get("current", 0)
    best = streak_data.get("best", 0)
    if streak_data.get("broken"):
        lines.append(f"💔 Стрик сброшен. Лучший был: {best} дней")
    else:
        lines.append(f"🔥 Стрик: {current} дней")
    return "\n".join(lines)


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(CommandHandler("streak", streak))
    app.add_handler(CommandHandler("task", task))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_message))

    from scheduler import setup_scheduler
    setup_scheduler(app)

    logger.info("Бот запущен")
    app.run_polling()


if __name__ == "__main__":
    main()
