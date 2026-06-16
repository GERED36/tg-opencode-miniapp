"""Configuration module. Loads settings from .env file. Interactive setup on first run."""

import os
from pathlib import Path

from dotenv import load_dotenv, set_key

ENV_PATH = Path(__file__).parent / ".env"

load_dotenv(ENV_PATH)

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
OPENCODE_WORK_DIR: str = os.getenv("OPENCODE_WORK_DIR", str(Path.cwd()))
OPENCODE_BIN_PATH: str = os.getenv("OPENCODE_BIN_PATH", "")
GOOGLE_STT_LANGUAGE: str = os.getenv("GOOGLE_STT_LANGUAGE", "ru-RU")
AGENTS_DB_PATH: str = os.getenv("AGENTS_DB_PATH", str(Path(__file__).parent / "connected_agents.json"))

ADMIN_IDS_RAW: str = os.getenv("ADMIN_IDS", "")
ADMIN_IDS: list[int] = []
for part in ADMIN_IDS_RAW.split(","):
    part = part.strip()
    if part:
        try:
            ADMIN_IDS.append(int(part))
        except ValueError:
            pass

RATE_LIMIT_PER_MINUTE: int = 10


def is_admin(user_id: int) -> bool:
    if not ADMIN_IDS:
        return True
    return user_id in ADMIN_IDS


def _setup_wizard() -> None:
    global BOT_TOKEN

    print("\n" + "=" * 50)
    print("  First run setup")
    print("=" * 50)

    if not BOT_TOKEN:
        print("\nTo create a bot, message @BotFather in Telegram.")
        token = input("Enter BOT_TOKEN: ").strip()
        if not token:
            print("Error: BOT_TOKEN is required.")
            exit(1)
        set_key(str(ENV_PATH), "BOT_TOKEN", token)
        BOT_TOKEN = token

    print("\n" + "=" * 50)
    print("  Setup complete! Starting bot...")
    print("=" * 50 + "\n")


def validate_config() -> None:
    global BOT_TOKEN

    if not BOT_TOKEN:
        _setup_wizard()

    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is not set")
