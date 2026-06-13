import os
import logging
from groq import Groq
from config import GROQ_API_KEY

logger = logging.getLogger(__name__)
groq_client = Groq(api_key=GROQ_API_KEY)


async def transcribe_voice(voice, context) -> str | None:
    voice_oga = f"voice_{voice.file_id}.oga"
    voice_mp3 = f"voice_{voice.file_id}.mp3"

    try:
        # Скачиваем файл
        file = await context.bot.get_file(voice.file_id)
        await file.download_to_drive(voice_oga)

        # Конвертируем oga -> mp3
        ret = os.system(f"ffmpeg -y -i {voice_oga} -ar 16000 {voice_mp3} -loglevel quiet")
        if ret != 0:
            logger.error("ffmpeg конвертация не удалась")
            return None

        # Отправляем в Groq Whisper
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
