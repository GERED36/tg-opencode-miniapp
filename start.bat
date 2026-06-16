@echo off
chcp 65001 >nul
title Telegram OpenCode Bot

where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python не найден. Установите Python 3.10+
    pause
    exit /b 1
)

if not exist ".env" (
    echo .env не найден. Создаю...
    echo BOT_TOKEN= > .env
)

echo Устанавливаю зависимости...
pip install -r requirements.txt

echo.
echo Запускаю бота...
python bot.py

pause
