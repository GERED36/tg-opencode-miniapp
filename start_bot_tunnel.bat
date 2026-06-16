@echo off
echo Starting bot.py in background...
start /B python bot.py > bot_tunnel.log 2>&1
timeout /t 3 /nobreak >nul
echo Starting ngrok on port 8080...
ngrok http 8080 --log=stdout > ngrok.log 2>&1
echo.
echo Bot and ngrok starting. Check URLs:
echo - ngrok dashboard: http://127.0.0.1:4040
echo - ngrok URL:   find it in ngrok.log or at http://127.0.0.1:4040/status
echo.
echo Set VITE_HUB_URL=wss://YOUR_NGROK_URL.ngrok-free.app/ws on Vercel:
echo https://vercel.com/dashboard -^> tma -^> Settings -^> Environment Variables
echo.
pause
