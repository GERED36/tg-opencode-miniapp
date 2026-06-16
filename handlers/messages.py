import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from aiogram import F

from config import GOOGLE_STT_LANGUAGE
from services.agent_bridge import AgentBridge
from services.session_manager import SessionManager
from utils.formatter import _send, _typing_loop, _is_limit_error

logger = logging.getLogger(__name__)

router = Router()

FILES_DIR = Path(__file__).resolve().parent.parent / "bot_files"


def setup_message_handlers(dp: Dispatcher, bridge: AgentBridge, session_manager: SessionManager) -> None:
    dp.include_router(router)

    @dp.message(F.text)
    async def handle_text(message: Message) -> None:
        text = message.text
        if not text or text.startswith("/"):
            return

        user_id = message.from_user.id
        if not bridge.is_connected(user_id):
            await message.answer("❌ Ваш ПК не подключён. Отправьте /start для инструкций.")
            return

        if message.reply_to_message and message.reply_to_message.text:
            text = f"[Ответ на сообщение]: {message.reply_to_message.text}\n\n[Мой вопрос]: {text}"

        has_session = session_manager.has_session(user_id)
        ctx = session_manager.get_context(user_id)

        typing_task = asyncio.create_task(_typing_loop(message.bot, message.chat.id))
        try:
            if not has_session and ctx:
                await bridge.ask_agent(user_id, ctx, continue_session=False)
                session_manager.mark_session_started(user_id)
                response = await bridge.ask_agent(user_id, text, continue_session=True)
            else:
                response = await bridge.ask_agent(user_id, text, continue_session=has_session)
                if not has_session:
                    session_manager.mark_session_started(user_id)

            if _is_limit_error(response):
                summary = await bridge.ask_agent(
                    user_id,
                    f"Суммаризируй диалог кратко, выделив суть. Вот последнее сообщение пользователя: {text}",
                    continue_session=True,
                )
                session_manager.reset_session(user_id)
                ctx_text = f"[Сжатый контекст предыдущего диалога]: {summary}\n\n[Новый вопрос]: {text}"
                response = await bridge.ask_agent(user_id, ctx_text, continue_session=False)
                session_manager.mark_session_started(user_id)
        finally:
            typing_task.cancel()

        await _send(message, response)

    @dp.message(F.voice)
    async def handle_voice(message: Message) -> None:
        if not message.voice:
            return

        user_id = message.from_user.id
        if not bridge.is_connected(user_id):
            await message.answer("❌ Ваш ПК не подключён. Отправьте /start для инструкций.")
            return

        await message.bot.send_chat_action(message.chat.id, "record_voice")
        try:
            from stt import process_voice

            text = await process_voice(
                file_id=message.voice.file_id,
                bot=message.bot,
                language=GOOGLE_STT_LANGUAGE,
            )
            if not text:
                await message.answer("🎤 Не удалось распознать голосовое сообщение.")
                return
            await message.answer(f"🎤 Распознано: {text}")

            has_session = session_manager.has_session(user_id)
            ctx = session_manager.get_context(user_id)

            typing_task = asyncio.create_task(_typing_loop(message.bot, message.chat.id))
            try:
                if not has_session and ctx:
                    await bridge.ask_agent(user_id, ctx, continue_session=False)
                    session_manager.mark_session_started(user_id)
                    response = await bridge.ask_agent(user_id, text, continue_session=True)
                else:
                    response = await bridge.ask_agent(user_id, text, continue_session=has_session)
                    if not has_session:
                        session_manager.mark_session_started(user_id)
            finally:
                typing_task.cancel()
            await _send(message, response)
        except Exception as e:
            logger.exception("Error processing voice")
            await message.answer(f"❌ Ошибка: {e}")

    async def _download_tg_file(bot: Bot, file_id: str, ext: str = "") -> str:
        file_info = await bot.get_file(file_id)
        suffix = ext or Path(file_info.file_path).suffix
        local_name = f"{file_id}{suffix}"
        local_path = FILES_DIR / local_name
        await bot.download_file(file_info.file_path, destination=str(local_path))
        return local_name

    async def _process_media(
        message: Message,
        file_id: str,
        ext: str,
        media_type: str,
        bridge: AgentBridge,
        session_manager: SessionManager,
    ) -> None:
        user_id = message.from_user.id
        caption = message.caption or ""

        has_session = session_manager.has_session(user_id)
        ctx = session_manager.get_context(user_id)

        local_name = await _download_tg_file(message.bot, file_id, ext)
        server_host = "127.0.0.1"
        file_url = f"http://{server_host}:8080/files/{local_name}"
        text = f"[{media_type}: {file_url}]\n{caption}" if caption else f"[{media_type}: {file_url}]"

        typing_task = asyncio.create_task(_typing_loop(message.bot, message.chat.id))
        try:
            try:
                if not has_session and ctx:
                    await bridge.ask_agent(user_id, ctx, continue_session=False)
                    session_manager.mark_session_started(user_id)
                    response = await bridge.ask_agent(user_id, text, continue_session=True, files=[file_url])
                else:
                    response = await bridge.ask_agent(user_id, text, continue_session=has_session, files=[file_url])
                    if not has_session:
                        session_manager.mark_session_started(user_id)
            except Exception as e:
                err = str(e).lower()
                if "does not support image" in err or "image input" in err:
                    fallback = f"[{media_type} not supported by model]\n{caption}" if caption else f"[{media_type} not supported by model]"
                    if not has_session and ctx:
                        await bridge.ask_agent(user_id, ctx, continue_session=False)
                        session_manager.mark_session_started(user_id)
                        response = await bridge.ask_agent(user_id, fallback, continue_session=True)
                    else:
                        response = await bridge.ask_agent(user_id, fallback, continue_session=has_session)
                        if not has_session:
                            session_manager.mark_session_started(user_id)
                else:
                    raise
            await _send(message, response)
        except Exception as e:
            if "does not support image" not in str(e).lower() and "image input" not in str(e).lower():
                logger.exception("Error processing %s", media_type)
                await message.answer(f"❌ Ошибка: {e}")
        finally:
            typing_task.cancel()

    @dp.message(F.photo)
    async def handle_photo(message: Message) -> None:
        if not message.photo:
            return

        user_id = message.from_user.id
        if not bridge.is_connected(user_id):
            await message.answer("❌ Ваш ПК не подключён. Отправьте /start для инструкций.")
            return

        photo = message.photo[-1]
        await _process_media(message, photo.file_id, ".jpg", "Image", bridge, session_manager)

    @dp.message(F.video)
    async def handle_video(message: Message) -> None:
        if not message.video:
            return

        user_id = message.from_user.id
        if not bridge.is_connected(user_id):
            await message.answer("❌ Ваш ПК не подключён. Отправьте /start для инструкций.")
            return

        await _process_media(message, message.video.file_id, ".mp4", "Video", bridge, session_manager)

    @dp.message(F.document)
    async def handle_document(message: Message) -> None:
        if not message.document:
            return

        user_id = message.from_user.id
        if not bridge.is_connected(user_id):
            await message.answer("❌ Ваш ПК не подключён. Отправьте /start для инструкций.")
            return

        await _process_media(message, message.document.file_id, "", "File", bridge, session_manager)
