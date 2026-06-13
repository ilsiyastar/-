import os
import logging
from config import GROQ_API_KEY

logger = logging.getLogger(__name__)


def _get_groq_client():
    """Создаём клиент лениво — только когда нужен."""
    from groq import Groq
    return Groq(api_key=GROQ_API_KEY)


async def transcribe_voice(voice, context) -> str | None:
    voice_oga = f"voice_{voice.file_id}.oga"
    voice_mp3 = f"voice_{voice.file_id}.mp3"

    try:
        groq_client = _get_groq_client()

        file = await context.bot.get_file(voice.file_id)
        await file.download_to_drive(voice_oga)

        ret = os.system(f"ffmpeg -y -i {voice_oga} -ar 16000 {voice_mp3} -loglevel quiet")
        if ret != 0:
            logger.error("ffmpeg конвертация не удалась")
            return None

        with open(voice_mp3, "rb") as f:
            transcription = groq_client.audio.transcriptions.create(
                file=(voice_mp3, f.read()),
                model="whisper-large-v3",
                language="ru"
            )
        return transcription.text

    except Exception as e:
        logger.error(f"Ошибка транскрипции: {e}")
        return None
    finally:
        for path in [voice_oga, voice_mp3]:
            if os.path.exists(path):
                os.remove(path)
