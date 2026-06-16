import os

HUB_PORT: int = int(os.getenv("PORT", os.getenv("HUB_PORT", "8081")))
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
JWT_SECRET: str = os.getenv("JWT_SECRET", os.urandom(32).hex())
HOST: str = os.getenv("HOST", "0.0.0.0")
TMA_ORIGIN: str = os.getenv("TMA_ORIGIN", "*")
