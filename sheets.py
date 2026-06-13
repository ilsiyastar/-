import json
import logging
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_FILE = "data.json"


def _load() -> dict:
    if Path(DATA_FILE).exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"habits": [], "sales": []}


def _save(data: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_habits(habits_dict: dict) -> dict:
    try:
        data = _load()
        today = date.today().isoformat()
        habits = data["habits"]

        keys = ["шаги", "медитация", "йога", "английский", "чтение"]
        done = sum(1 for k in keys if habits_dict.get(k))
        day_ok = done >= 3

        # Если сегодня уже есть запись — обновляем
        if habits and habits[-1]["дата"] == today:
            habits.pop()

        # Пересчёт стрика
        current_streak = 0
        best_streak = 0
        broken = False

        if habits:
            last = habits[-1]
            last_date = date.fromisoformat(last["дата"])
            delta = (date.today() - last_date).days
            last_best = last.get("стрик_лучший", 0)
            last_current = last.get("стрик_текущий", 0)
            last_day_ok = last.get("день_засчитан", False)

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

        habits.append({
            "дата": today,
            "шаги": habits_dict.get("шаги", False),
            "медитация": habits_dict.get("медитация", False),
            "йога": habits_dict.get("йога", False),
            "английский": habits_dict.get("английский", False),
            "чтение": habits_dict.get("чтение", False),
            "выполнено_из_5": done,
            "день_засчитан": day_ok,
            "стрик_текущий": current_streak,
            "стрик_лучший": best_streak,
        })

        _save(data)
        return {"current": current_streak, "best": best_streak, "broken": broken}

    except Exception as e:
        logger.error(f"Ошибка сохранения привычек: {e}")
        return {"current": 0, "best": 0, "broken": False}


def get_current_streak() -> int:
    data = _load()
    habits = data.get("habits", [])
    if habits:
        return habits[-1].get("стрик_текущий", 0)
    return 0


def get_best_streak() -> int:
    data = _load()
    habits = data.get("habits", [])
    if habits:
        return habits[-1].get("стрик_лучший", 0)
    return 0


def has_habits_today() -> bool:
    data = _load()
    habits = data.get("habits", [])
    if habits:
        return habits[-1]["дата"] == date.today().isoformat()
    return False


def get_week_summary() -> str:
    data = _load()
    habits = data.get("habits", [])
    last7 = habits[-7:] if len(habits) >= 7 else habits
    n = len(last7)

    if n == 0:
        return "Ещё нет данных за эту неделю"

    keys = ["шаги", "медитация", "йога", "английский", "чтение"]
    emojis = ["🚶", "🧘", "🕉", "🇬🇧", "📚"]
    names = ["Шаги", "Медитация", "Йога", "Английский", "Чтение"]

    lines = [f"Итог недели ({n} дней):"]
    counts = []
    for key, name, emoji in zip(keys, names, emojis):
        count = sum(1 for r in last7 if r.get(key))
        counts.append(count)
        pct = int(count / n * 100)
        lines.append(f"{emoji} {name} — {count}/{n} ({pct}%)")

    avg = int(sum(counts) / (len(counts) * n) * 100) if n > 0 else 0
    lines.append(f"\nСредний балл: {avg}%")
    lines.append(f"🔥 Текущий стрик: {get_current_streak()} дней")
    lines.append(f"🏆 Лучший стрик: {get_best_streak()} дней")
    return "\n".join(lines)


def save_sales(task: str, answer: str, review: str, score):
    try:
        data = _load()
        data["sales"].append({
            "дата": date.today().isoformat(),
            "задание": task,
            "ответ": answer,
            "разбор": review,
            "оценка": score,
        })
        _save(data)
    except Exception as e:
        logger.error(f"Ошибка сохранения продаж: {e}")


def get_sales_history() -> str:
    data = _load()
    sales = data.get("sales", [])
    last5 = sales[-5:] if len(sales) >= 5 else sales

    if not last5:
        return "Ещё нет заданий по продажам"

    lines = ["Последние задания:\n"]
    for i, row in enumerate(reversed(last5), 1):
        task_preview = row["задание"][:60] + "..." if len(row["задание"]) > 60 else row["задание"]
        score = row.get("оценка") or "—"
        lines.append(f"{i}. {row['дата']} | Оценка: {score}/5\n{task_preview}\n")

    return "\n".join(lines)
