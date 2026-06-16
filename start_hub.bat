@echo off
cd /d "%~dp0"
pip install -r hub\requirements.txt
python -m hub.hub
pause
