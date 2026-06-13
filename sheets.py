import gspread
from datetime import date, timedelta
from google.oauth2.service_account import Credentials
from config import GOOGLE_SHEETS_ID, GOOGLE_CREDENTIALS_PATH
import logging

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


def _get_client():
    creds = Credentials.from_service_account_file(GOOGLE_CREDENTIALS_PATH, scopes=SCOPES)
    return gspread.authorize(creds)


def _get_sheets():
    gc = _get_client()
    spreadsheet = gc.open_by_key(GOOGLE_SHEETS_ID)

    # Создаём листы если нет
    sheet_names = [s.title for s in spreadsheet.worksheets()]

    if "habits" not in sheet_names:
        habits = spreadsheet.add_worksheet("habits", rows=1000, cols=11)
        habits.append_row(["дата", "шаги", "медитация", "йога", "английский",
                           "чтение", "выполнено_из_5", "день_засчитан",
                           "стрик_текущий", "стрик_лучший"])
    else:
        habits = spreadsheet.worksheet("habits")

    if "sales" not in sheet_names:
        sales = spreadsheet.add_worksheet("sales", rows=1000, cols=5)
        sales.append_row(["дата", "задание", "ответ", "разбор", "оценка"])
    else:
        sales = spreadsheet.worksheet("sales")

    return habits, sales


def save_habits(habits_dict: dict) -> dict:
    try:
        habits_sheet, _ = _get_sheets()
        today = date.today().isoformat()

        # Считаем выполненные
        keys = ["шаги", "медитация", "йога", "английский", "чтение"]
        done = sum(1 for k in keys if habits_dict.get(k))
        day_ok = done >= 3

        # Читаем последнюю строку для пересчёта стрика
        all_rows = habits_sheet.get_all_values()
        data_rows = [r for r in all_rows[1:] if r[0]]  # пропускаем заголовок

        current_streak = 0
        best_streak = 0
        broken = False

        if data_rows:
            last = data_rows[-1]
            last_date_str = last[0]
            last_current = int(last[8]) if last[8] else 0
            last_best = int(last[9]) if last[9] else 0
            last_day_ok = last[7] == "TRUE" or last[7] == "True" or last[7] is True

            # Если сегодня уже есть запись — обновляем
            if last_date_str == today:
                # Удаляем последнюю строку и перезаписываем
                habits_sheet.delete_rows(len(all_rows))
                current_streak = last_current
                best_streak = last_best
            else:
                # Пересчёт стрика
                last_date = date.fromisoformat(last_date_str)
                delta = (date.today() - last_date).days

                if delta == 1 and last_day_ok:
                    current_streak = last_current + 1
                elif delta == 1 and not last_day_ok:
                    current_streak = 0
                    broken = True
                else:
                    current_streak = 0
                    broken = last_current > 0

                best_streak = max(last_best, current_streak)
        else:
            current_streak = 1 if day_ok else 0
            best_streak = current_streak

        best_streak = max(best_streak, current_streak)

        row = [
            today,
            str(habits_dict.get("шаги", False)),
            str(habits_dict.get("медитация", False)),
            str(habits_dict.get("йога", False)),
            str(habits_dict.get("английский", False)),
            str(habits_dict.get("чтение", False)),
            done,
            str(day_ok),
            current_streak,
            best_streak
        ]
        habits_sheet.append_row(row)

        return {"current": current_streak, "best": best_streak, "broken": broken}

    except Exception as e:
        logger.error(f"Ошибка сохранения привычек: {e}")
        return {"current": 0, "best": 0, "broken": False}


def get_current_streak() -> int:
    try:
        habits_sheet, _ = _get_sheets()
        all_rows = habits_sheet.get_all_values()
        data_rows = [r for r in all_rows[1:] if r[0]]
        if data_rows:
            return int(data_rows[-1][8]) if data_rows[-1][8] else 0
        return 0
    except Exception as e:
        logger.error(f"Ошибка чтения стрика: {e}")
        return 0


def get_best_streak() -> int:
    try:
        habits_sheet, _ = _get_sheets()
        all_rows = habits_sheet.get_all_values()
        data_rows = [r for r in all_rows[1:] if r[0]]
        if data_rows:
            return int(data_rows[-1][9]) if data_rows[-1][9] else 0
        return 0
    except Exception as e:
        logger.error(f"Ошибка чтения лучшего стрика: {e}")
        return 0


def get_week_summary() -> str:
    try:
        habits_sheet, _ = _get_sheets()
        all_rows = habits_sheet.get_all_values()
        data_rows = [r for r in all_rows[1:] if r[0]]
        last7 = data_rows[-7:] if len(data_rows) >= 7 else data_rows
        n = len(last7)

        if n == 0:
            return "Ещё нет данных за эту неделю"

        keys = ["шаги", "медитация", "йога", "английский", "чтение"]
        cols = [1, 2, 3, 4, 5]
        counts = []
        for col in cols:
            c = sum(1 for r in last7 if (r[col] == "True" or r[col] == "TRUE"))
            counts.append(c)

        current = get_current_streak()
        best = get_best_streak()

        lines = [f"Итог недели ({n} дней):"]
        emojis = ["🚶", "🧘", "🕉", "🇬🇧", "📚"]
        names = ["Шаги", "Медитация", "Йога", "Английский", "Чтение"]
        for i, (name, emoji, count) in enumerate(zip(names, emojis, counts)):
            pct = int(count / n * 100)
            lines.append(f"{emoji} {name} — {count}/{n} ({pct}%)")

        avg = int(sum(counts) / (len(counts) * n) * 100)
        lines.append(f"\nСредний балл: {avg}%")
        lines.append(f"🔥 Текущий стрик: {current} дней")
        lines.append(f"🏆 Лучший стрик: {best} дней")
        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Ошибка недельного итога: {e}")
        return "Не удалось получить итог"


def save_sales(task: str, answer: str, review: str, score: int | None):
    try:
        _, sales_sheet = _get_sheets()
        today = date.today().isoformat()
        sales_sheet.append_row([today, task, answer, review, score or ""])
    except Exception as e:
        logger.error(f"Ошибка сохранения продаж: {e}")


def has_habits_today() -> bool:
    try:
        habits_sheet, _ = _get_sheets()
        all_rows = habits_sheet.get_all_values()
        data_rows = [r for r in all_rows[1:] if r[0]]
        if not data_rows:
            return False
        return data_rows[-1][0] == date.today().isoformat()
    except Exception:
        return False


def get_sales_history() -> str:
    try:
        _, sales_sheet = _get_sheets()
        all_rows = sales_sheet.get_all_values()
        data_rows = [r for r in all_rows[1:] if r[0]]
        last5 = data_rows[-5:] if len(data_rows) >= 5 else data_rows

        if not last5:
            return "Ещё нет заданий по продажам"

        lines = ["Последние задания:\n"]
        for i, row in enumerate(reversed(last5), 1):
            date_str = row[0]
            task_preview = row[1][:60] + "..." if len(row[1]) > 60 else row[1]
            score = row[4] if row[4] else "—"
            lines.append(f"{i}. {date_str} | Оценка: {score}/5\n{task_preview}\n")

        return "\n".join(lines)
    except Exception as e:
        logger.error(f"Ошибка истории продаж: {e}")
        return "Не удалось получить историю"
