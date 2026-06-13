import json
import anthropic
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

HABITS_PROMPT = """Яна отчитывается о привычках за день.
Определи какие выполнены из её сообщения.

Привычки:
- шаги (шаги, ходила, прошла, прогулка, тысяч шагов, к шагов)
- медитация (медитация, медитировала, тумо)
- йога (йога, занималась йогой)
- английский (английский, english, занималась языком)
- чтение (читала, чтение, книга)

Верни ТОЛЬКО валидный JSON без markdown, без пояснений, одной строкой:
{"шаги":true,"медитация":false,"йога":true,"английский":false,"чтение":true}

Если сообщение не про привычки — верни:
{"error":"not_habits"}"""

SALES_TASK_PROMPT = """Ты тренер по продажам luxury недвижимости в Дубае.
Яна продаёт объекты от $1M, длинный цикл, продажи онлайн.

Сгенерируй одну задачу. Чередуй типы (Возражение/Ситуация/Психология/Питч).

Формат строго:
Строка 1: тип задачи одним словом
Строка 2: пустая
Строки 3+: сама задача коротко и конкретно
Последняя строка: "Отвечай голосом или текстом 👇"

На русском языке."""

SALES_REVIEW_PROMPT = """Ты тренер по продажам luxury недвижимости в Дубае.

Задача была: {task}
Ответ Яны: {answer}

Разбери честно и коротко:
— Что сработало
— Что можно усилить
— Конкретная альтернатива

Последние две строки ОБЯЗАТЕЛЬНО:
---
Оценка: X/5"""


def process_habits(text: str) -> dict | None:
    for attempt in range(2):
        try:
            extra = " Верни ТОЛЬКО JSON, никакого текста." if attempt > 0 else ""
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=200,
                messages=[{"role": "user", "content": HABITS_PROMPT + extra + f"\n\nСообщение: {text}"}]
            )
            raw = response.content[0].text.strip()
            data = json.loads(raw)
            if "error" in data:
                return None
            return data
        except (json.JSONDecodeError, Exception):
            continue
    return None


def process_sales_review(task: str, answer: str) -> str:
    prompt = SALES_REVIEW_PROMPT.format(task=task, answer=answer)
    for attempt in range(2):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            text = response.content[0].text.strip()
            if "Оценка:" in text:
                return text
            if attempt == 0:
                # Повторный запрос с напоминанием
                retry_prompt = prompt + "\n\nВАЖНО: в конце обязательно добавь строку 'Оценка: X/5'"
                response2 = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=500,
                    messages=[{"role": "user", "content": retry_prompt}]
                )
                return response2.content[0].text.strip()
        except Exception as e:
            continue
    return "Разбор не удался, попробуй ещё раз"


def generate_sales_task() -> str:
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            messages=[{"role": "user", "content": SALES_TASK_PROMPT}]
        )
        return response.content[0].text.strip()
    except Exception as e:
        return "Ситуация\n\nКлиент посмотрел объект, сказал 'интересно' и пропал на неделю. Как вернуть контакт?\n\nОтвечай голосом или текстом 👇"
