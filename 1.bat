@echo off
chcp 65001 >nul
title BotoLinkPro — Главный запуск

echo 🚀 Проверка окружения...
echo --------------------------------------------------

:: Переходим в папку, где лежит сам батник
cd /d "%~dp0"

:: 1. Проверяем наличие Python
if not exist ".venv\Scripts\python.exe" (
    echo ❌ ОШИБКА: Не найдена папка .venv
    echo Текущий путь: %cd%
    pause
    exit
)

:: 2. Проверяем наличие ГЛАВНОГО main.py (в корне)
if not exist "main.py" (
    echo ❌ ОШИБКА: Не найден ГЛАВНЫЙ файл main.py в корне!
    echo Проверьте, что батник лежит в одной папке с main.py
    pause
    exit
)

echo ✅ Всё найдено. Запускаю основной проект...
echo --------------------------------------------------

:: Запускаем именно главный файл в корне
".venv\Scripts\python.exe" "main.py"

if %errorlevel% neq 0 (
    echo.
    echo ❌ Произошла ошибка при работе скрипта!
    pause
)