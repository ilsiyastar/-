import os
import logging
import subprocess
from config import GROQ_API_KEY

logger = logging.getLogger(__name__)


def _get_groq_client():
    from groq import Groq
    return Groq(api_key=GROQ_API_KEY)


async def transcribe_voice(voice, context) -> str | None:
    voice_oga = f"/tmp/voice_{voice.file_id}.oga"
    voice_mp3 = f"/tmp/voice_{voice.file_id}.mp3"

    try:
        # Скачиваем файл
        file = await context.bot.get_file(voice.file_id)
        await file.download_to_drive(voice_oga)
        logger.info(f"Голос скачан: {voice_oga}, размер: {os.path.getsize(voice_oga)} байт")

        # Пробуем отправить сразу без конвертации
        try:
            groq_client = _get_groq_client()
            with open(voice_oga, "rb") as f:
                transcription = groq_client.audio.transcriptions.create(
                    file=(f"audio.oga", f.read()),
                    model="whisper-large-v3",
                    language="ru"
                )
            logger.info(f"Транскрипция без конвертации: {transcription.text}")
            return transcription.text
        except Exception as e:
            logger.warning(f"Без конвертации не вышло: {e}, пробуем ffmpeg...")

        # Конвертируем через ffmpeg
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", voice_oga, "-ar", "16000", voice_mp3],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            logger.error(f"ffmpeg ошибка: {result.stderr}")
            return None

        logger.info(f"Конвертация успешна: {voice_mp3}")

        groq_client = _get_groq_client()
        with open(voice_mp3, "rb") as f:
            transcription = groq_client.audio.transcriptions.create(
                file=(f"audio.mp3", f.read()),
                model="whisper-large-v3",
                language="ru"
            )
        logger.info(f"Транскрипция: {transcription.text}")
        return transcription.text

    except Exception as e:
        logger.error(f"Ошибка транскрипции: {e}", exc_info=True)
        return None
    finally:
        for path in [voice_oga, voice_mp3]:
            if os.path.exists(path):
                os.remove(path)
