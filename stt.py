"""Speech-to-Text module. Downloads voice messages, converts, and transcribes."""

import logging
import tempfile
from pathlib import Path

from pydub import AudioSegment
import speech_recognition as sr
from aiogram import Bot

from config import GOOGLE_STT_LANGUAGE

logger = logging.getLogger(__name__)

# Temp directory for audio files
TEMP_DIR = Path(tempfile.gettempdir()) / "tg_opencode_bot"


async def download_voice(file_id: str, bot: Bot) -> Path:
    """
    Download a voice message file from Telegram.

    Args:
        file_id: Telegram file_id of the voice message.
        bot: Aiogram Bot instance.

    Returns:
        Path to the downloaded OGG file.
    """
    TEMP_DIR.mkdir(exist_ok=True)

    # Get file info from Telegram
    file_info = await bot.get_file(file_id)
    ogg_path = TEMP_DIR / f"{file_id}.ogg"

    # Download file
    await bot.download_file(file_info.file_path, destination=str(ogg_path))
    logger.info("Downloaded voice to %s", ogg_path)

    return ogg_path


def convert_ogg_to_wav(ogg_path: Path) -> Path:
    """
    Convert OGG audio file to WAV format using pydub/FFmpeg.

    Args:
        ogg_path: Path to the OGG file.

    Returns:
        Path to the converted WAV file.
    """
    wav_path = ogg_path.with_suffix(".wav")

    # Load OGG and export as WAV
    audio = AudioSegment.from_ogg(str(ogg_path))
    audio.export(str(wav_path), format="wav")
    logger.info("Converted %s to %s", ogg_path.name, wav_path.name)

    return wav_path


def transcribe(wav_path: Path, language: str = GOOGLE_STT_LANGUAGE) -> str:
    """
    Transcribe a WAV audio file using Google Speech Recognition.

    Args:
        wav_path: Path to the WAV file.
        language: Language code for transcription (e.g., 'ru-RU', 'en-US').

    Returns:
        Transcribed text.
    """
    recognizer = sr.Recognizer()

    with sr.AudioFile(str(wav_path)) as source:
        audio_data = recognizer.record(source)

    try:
        # Use Google's free speech recognition API
        text = recognizer.recognize_google(audio_data, language=language)
        logger.info("Transcribed: %s", text[:100])
        return text
    except sr.UnknownValueError:
        logger.warning("Google STT could not understand the audio")
        return ""
    except sr.RequestError as e:
        logger.error("Google STT request failed: %s", e)
        raise RuntimeError(f"Ошибка сервиса распознавания: {e}") from e


async def process_voice(file_id: str, bot: Bot, language: str = GOOGLE_STT_LANGUAGE) -> str:
    """
    Process a voice message: download, convert, and transcribe.

    Args:
        file_id: Telegram file_id of the voice message.
        bot: Aiogram Bot instance.
        language: Language code for transcription.

    Returns:
        Transcribed text, or empty string if transcription failed.
    """
    # Step 1: Download
    ogg_path = await download_voice(file_id, bot)

    # Step 2: Convert OGG → WAV
    wav_path = convert_ogg_to_wav(ogg_path)

    # Step 3: Transcribe
    text = transcribe(wav_path, language)

    # Cleanup temp files
    try:
        ogg_path.unlink(missing_ok=True)
        wav_path.unlink(missing_ok=True)
    except OSError:
        pass

    return text
