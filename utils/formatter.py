import hashlib
import html
import logging
import re
from asyncio import CancelledError, sleep

from aiogram import Bot
from aiogram.types import Message

logger = logging.getLogger(__name__)


def _format_code(text: str) -> str:
    text = re.sub(r'```(\w*)\n', r'<pre><code class="language-\1">', text)
    text = text.replace("```", "</code></pre>")
    text = re.sub(r'`([^`]+)`', r"<code>\1</code>", text)
    return text


def _replace_emoji(text: str, emoji_map: dict[str, str]) -> str:
    if not emoji_map:
        return text
    result: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        best_len = 0
        best_id = None
        for l in range(min(6, n - i), 0, -1):
            chunk = text[i : i + l]
            if chunk in emoji_map:
                best_len = l
                best_id = emoji_map[chunk]
                break
        if best_len:
            chunk = text[i : i + best_len]
            result.append(f'<tg-emoji emoji-id="{best_id}">{chunk}</tg-emoji>')
            i += best_len
        else:
            result.append(text[i])
            i += 1
    return "".join(result)


def _split_text(text: str, max_length: int = 4000) -> list[str]:
    if len(text) <= max_length:
        return [text]
    chunks: list[str] = []
    while text:
        if len(text) <= max_length:
            chunks.append(text)
            break
        split_pos = text.rfind("\n", 0, max_length)
        if split_pos == -1:
            split_pos = text.rfind(" ", 0, max_length)
        if split_pos == -1:
            split_pos = max_length
        chunks.append(text[:split_pos])
        text = text[split_pos:].lstrip("\n").lstrip()
    return chunks


def _encode_model_id(model_id: str, hash_map: dict[str, str]) -> str:
    encoded = model_id.replace("/", ".").replace(":", "_")
    if len(encoded) > 60:
        short_hash = hashlib.md5(model_id.encode()).hexdigest()[:8]
        encoded = f"m.{short_hash}"
        hash_map[encoded] = model_id
    return encoded


def _decode_model_id(encoded: str, hash_map: dict[str, str]) -> str:
    if encoded in hash_map:
        return hash_map[encoded]
    return encoded.replace(".", "/").replace("_", ":")


async def _typing_loop(bot: Bot, chat_id: int, interval: float = 4.0) -> None:
    try:
        while True:
            await bot.send_chat_action(chat_id, "typing")
            await sleep(interval)
    except CancelledError:
        pass


def _is_limit_error(response: str) -> bool:
    lower = response.lower()
    clues = [
        "token limit", "context length", "maximum context", "too many tokens",
        "limit reached", "context window", "max_tokens", "token budget",
        "слишком длинный", "превышен лимит", "контекст", "токенов",
    ]
    return any(c in lower for c in clues)


async def _send(message: Message, text: str, emoji_map: dict[str, str] | None = None) -> None:
    text = html.escape(text)
    text = text.replace("&lt;pre&gt;", "<pre>").replace("&lt;/pre&gt;", "</pre>")
    text = text.replace("&lt;code&gt;", "<code>").replace("&lt;/code&gt;", "</code>")
    text = _format_code(text)
    if emoji_map:
        text = _replace_emoji(text, emoji_map)
    for chunk in _split_text(text, 4000):
        await message.answer(chunk, parse_mode="HTML")
