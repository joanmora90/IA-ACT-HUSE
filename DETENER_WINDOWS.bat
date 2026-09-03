@echo off
title Detener AI Act Validator
cd /d "%~dp0"
docker compose down
echo AI Act Validator detenido.
pause
