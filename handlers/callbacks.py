import asyncio
import logging

from aiogram import Dispatcher, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram import F

from models_db import MODELS_DB, get_model_by_id, format_context_limit, format_capabilities, get_models_by_provider, get_free_models
from services.agent_bridge import AgentBridge
from utils.formatter import _encode_model_id, _decode_model_id, _typing_loop

logger = logging.getLogger(__name__)

router = Router()
_model_hash_map: dict[str, str] = {}


def setup_callbacks(dp: Dispatcher, bridge: AgentBridge) -> None:
    dp.include_router(router)

    @dp.callback_query(F.data.startswith("model_filter:"))
    async def callback_model_filter(callback: CallbackQuery) -> None:
        data = callback.data.split(":")
        filter_type = data[1]
        page = int(data[2]) if len(data) > 2 else 0
        await callback.answer()

        if filter_type == "free":
            models = get_free_models()
            title = "🆓 **Бесплатные модели:**"
        else:
            models = MODELS_DB
            title = "📋 **Все модели:**"

        per_page = 25
        total_pages = (len(models) + per_page - 1) // per_page
        start = page * per_page
        end = min(start + per_page, len(models))
        page_models = models[start:end]

        keyboard: list[list[InlineKeyboardButton]] = []
        for model in page_models:
            params_text = f" ({model.parameters})" if model.parameters != "Unknown" else ""
            context_text = format_context_limit(model.context_limit)
            caps = format_capabilities(model)
            button_text = f"{caps} {model.name}{params_text} [{context_text}]"
            encoded = _encode_model_id(model.model_id, _model_hash_map)
            keyboard.append([InlineKeyboardButton(text=button_text, callback_data=f"model:{encoded}")])

        nav_row: list[InlineKeyboardButton] = []
        if page > 0:
            nav_row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"model_filter:{filter_type}:{page-1}"))
        nav_row.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="model_noop"))
        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"model_filter:{filter_type}:{page+1}"))
        keyboard.append(nav_row)
        keyboard.append([InlineKeyboardButton(text="🏠 Меню", callback_data="model_back")])

        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(
            f"{title} (стр. {page+1}/{total_pages})",
            reply_markup=markup,
            parse_mode="Markdown",
        )

    @dp.callback_query(F.data.startswith("model_provider:"))
    async def callback_model_provider(callback: CallbackQuery) -> None:
        data = callback.data.split(":")
        provider = data[1]
        page = int(data[2]) if len(data) > 2 else 0
        await callback.answer()

        models = get_models_by_provider(provider)
        provider_names = {
            "opencode": "📌 OpenCode",
            "google": "🔷 Google",
            "openai": "🟢 OpenAI",
            "openrouter": "🟣 OpenRouter",
        }
        title = f"{provider_names.get(provider, provider)} **модели:**"

        per_page = 25
        total_pages = (len(models) + per_page - 1) // per_page
        start = page * per_page
        end = min(start + per_page, len(models))
        page_models = models[start:end]

        keyboard: list[list[InlineKeyboardButton]] = []
        for model in page_models:
            params_text = f" ({model.parameters})" if model.parameters != "Unknown" else ""
            context_text = format_context_limit(model.context_limit)
            caps = format_capabilities(model)
            button_text = f"{caps} {model.name}{params_text} [{context_text}]"
            encoded = _encode_model_id(model.model_id, _model_hash_map)
            keyboard.append([InlineKeyboardButton(text=button_text, callback_data=f"model:{encoded}")])

        nav_row: list[InlineKeyboardButton] = []
        if page > 0:
            nav_row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"model_provider:{provider}:{page-1}"))
        nav_row.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="model_noop"))
        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"model_provider:{provider}:{page+1}"))
        keyboard.append(nav_row)
        keyboard.append([InlineKeyboardButton(text="🏠 Меню", callback_data="model_back")])

        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(
            f"{title} (стр. {page+1}/{total_pages})",
            reply_markup=markup,
            parse_mode="Markdown",
        )

    @dp.callback_query(F.data == "model_noop")
    async def callback_model_noop(callback: CallbackQuery) -> None:
        await callback.answer()

    @dp.callback_query(F.data == "model_back")
    async def callback_model_back(callback: CallbackQuery) -> None:
        await callback.answer()
        keyboard = [
            [InlineKeyboardButton(text="🆓 Free Models", callback_data="model_filter:free")],
            [InlineKeyboardButton(text="📌 OpenCode", callback_data="model_provider:opencode")],
            [InlineKeyboardButton(text="🔷 Google", callback_data="model_provider:google")],
            [InlineKeyboardButton(text="🟢 OpenAI", callback_data="model_provider:openai")],
            [InlineKeyboardButton(text="🟣 OpenRouter", callback_data="model_provider:openrouter")],
            [InlineKeyboardButton(text="📋 Все модели", callback_data="model_filter:all")],
        ]
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(
            "🧠 **Выберите провайдер моделей:**",
            reply_markup=markup,
            parse_mode="Markdown",
        )

    @dp.callback_query(F.data.startswith("model:"))
    async def callback_model_select(callback: CallbackQuery) -> None:
        encoded_id = callback.data.split(":", 1)[1]
        model_id = _decode_model_id(encoded_id, _model_hash_map)
        model = get_model_by_id(model_id)

        if not model:
            await callback.answer("❌ Модель не найдена.", show_alert=True)
            return

        user_id = callback.from_user.id
        if not bridge.is_connected(user_id):
            await callback.answer("❌ ПК не подключён.", show_alert=True)
            return

        await callback.answer()

        typing_task = asyncio.create_task(_typing_loop(callback.message.bot, callback.message.chat.id))
        try:
            result = await bridge.ask_agent(user_id, f"config set model {model_id}")
        finally:
            typing_task.cancel()

        params_text = f" ({model.parameters})" if model.parameters != "Unknown" else ""
        context_text = format_context_limit(model.context_limit)

        caps_list = []
        if model.supports_text:
            caps_list.append("📝 Текст")
        if model.supports_image:
            caps_list.append("🖼 Изображения")
        if model.supports_video:
            caps_list.append("🎬 Видео")
        if model.supports_file:
            caps_list.append("📁 Файлы")
        caps_text = "\n".join(caps_list) if caps_list else "❌ Нет"

        await callback.message.answer(
            f"✅ **Модель изменена:**\n\n"
            f"📝 Название: {model.name}{params_text}\n"
            f"📊 Контекст: {context_text}\n"
            f"🔗 ID: `{model_id}`\n\n"
            f"**Возможности:**\n{caps_text}\n\n"
            f"```\n{result}\n```",
            parse_mode="Markdown",
        )
