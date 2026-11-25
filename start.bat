@echo off
title Phong Bien Tap Van Ban 3D - AI Document Studio
cd /d "%~dp0"
echo Dang khoi dong Phong Bien Tap Van Ban 3D tai http://127.0.0.1:8080 ...
start "" http://127.0.0.1:8080
python server.py
pause
