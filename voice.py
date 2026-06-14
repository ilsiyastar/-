import os
import logging
from config import GROQ_API_KEY

logger = logging.getLogger(__name__)


def _get_groq_client():
    from groq import Groq
    return Groq(api_key=GROQ_API_KEY)


async def transcribe_voice(voice, context) -> str | None:
    voice_oga = f"/tmp/voice_{voice.file_id}.oga"

    try:
        # Скачиваем файл
        file = await context.bot.get_file(voice.file_id)
        await file.download_to_drive(voice_oga)
        logger.info(f"Голос скачан: {os.path.getsize(voice_oga)} байт")

        # .oga и .ogg — один формат, Groq принимает .ogg
        groq_client = _get_groq_client()
        with open(voice_oga, "rb") as f:
            transcription = groq_client.audio.transcriptions.create(
                file=("audio.ogg", f.read()),
                model="whisper-large-v3",
                language="ru"
            )

        logger.info(f"Транскрипция: {transcription.text}")
        return transcription.text

    except Exception as e:
        logger.error(f"Ошибка транскрипции: {e}", exc_info=True)
        return None
    finally:
        if os.path.exists(voice_oga):
            os.remove(voice_oga)
