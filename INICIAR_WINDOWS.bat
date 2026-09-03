@echo off
title AI Act Validator
cd /d "%~dp0"

where docker >nul 2>nul
if errorlevel 1 (
  echo Docker Desktop no esta instalado o no esta disponible.
  echo Instala o abre Docker Desktop y vuelve a intentarlo.
  pause
  exit /b 1
)

docker info >nul 2>nul
if errorlevel 1 (
  echo Docker Desktop no esta iniciado.
  echo Abre Docker Desktop, espera a que arranque y vuelve a intentarlo.
  pause
  exit /b 1
)

echo Iniciando AI Act Validator...
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 10; Start-Process 'http://localhost:8501'"
docker compose up --build
