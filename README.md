# Бот: трекер привычек + тренер по продажам

## Что делает бот
- Утром в 8:00 напоминает отметить привычки
- Вечером в 21:00 напоминает если не отметила
- Пн/Ср/Пт в 10:00 присылает задачу по продажам
- Принимает голосовые сообщения
- Считает стрики и сохраняет всё в Google Sheets

---

## Шаг 1 — Создать бота в Telegram

1. Открой Telegram, найди @BotFather
2. Напиши `/newbot`
3. Придумай имя бота (например: Habit Tracker Yana)
4. Придумай username (например: yana_habit_bot)
5. Сохрани токен — он выглядит так: `7234567890:AAFxxxxxxxxxxxxxxxx`

---

## Шаг 2 — Узнать свой chat_id

1. Найди в Telegram бота @userinfobot
2. Напиши ему `/start`
3. Он пришлёт твой ID — сохрани его

---

## Шаг 3 — Получить ключи API

**Anthropic (Claude):**
- Зайди на console.anthropic.com
- Settings → API Keys → Create Key
- Сохрани ключ

**Groq (для голоса):**
- Зайди на console.groq.com
- API Keys → Create API Key
- Сохрани ключ

---

## Шаг 4 — Настроить Google Sheets

1. Зайди на console.cloud.google.com
2. Создай новый проект
3. Включи API: Google Sheets API + Google Drive API
4. Перейди в Credentials → Service Account → Create
5. Скачай JSON файл — переименуй его в `credentials.json`
6. Создай Google таблицу на своём аккаунте
7. Из JSON файла скопируй `client_email`
8. Открой таблицу → Поделиться → вставь этот email → Редактор
9. Из URL таблицы скопируй ID (длинная строка между /d/ и /edit)

---

## Шаг 5 — Загрузить на GitHub

1. Зайди на github.com, создай новый репозиторий
2. Загрузи все файлы из этой папки КРОМЕ:
   - `.env` (его не загружать!)
   - `credentials.json` (его не загружать!)
3. Загружай: bot.py, config.py, state.py, claude_client.py, voice.py, sheets.py, scheduler.py, requirements.txt, Procfile

---

## Шаг 6 — Задеплоить на Railway

1. Зайди на railway.app → Login with GitHub
2. New Project → Deploy from GitHub repo
3. Выбери свой репозиторий
4. Перейди в Variables (переменные) и добавь:
   ```
   TELEGRAM_TOKEN = токен от BotFather
   ANTHROPIC_API_KEY = ключ Claude
   GROQ_API_KEY = ключ Groq
   GOOGLE_SHEETS_ID = ID таблицы
   OWNER_CHAT_ID = твой chat_id
   ```
5. В Settings → Secret Files → добавь файл:
   - Имя: `credentials.json`
   - Содержимое: вставь весь текст из JSON файла сервисного аккаунта
6. Нажми Deploy

---

## Проверка

После деплоя найди своего бота в Telegram и напиши `/start`

Если бот не отвечает — проверь Logs в Railway на ошибки

---

## Команды бота

- `/start` — приветствие
- `/итог` — итог недели по привычкам
- `/стрик` — текущий и лучший стрик
- `/задача` — получить задачу по продажам прямо сейчас
- `/история` — последние 5 заданий по продажам

Обычное сообщение или голосовое → отчёт о привычках
