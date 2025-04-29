@echo off
setlocal enabledelayedexpansion

:: Название проекта
set PROJECT_DIR=.
set VENV_DIR=venv
set REQUIREMENTS=%PROJECT_DIR%\requirements.txt
set WAD_FILE=%PROJECT_DIR%\conquest.wad

:: Включаем поддержку ANSI escape sequences для цветов (Windows 10+)
for /f "tokens=2 delims=: " %%i in ('"echo list ^| cmd"') do set "ANSI=%%i"

:: Цвета
set COLOR_RESET=[0m
set COLOR_GREEN=[32m
set COLOR_YELLOW=[33m
set COLOR_RED=[31m
set COLOR_CYAN=[36m
set COLOR_MAGENTA=[35m

:: Начало
echo %COLOR_CYAN%🛠 Проверка окружения VizDoom...%COLOR_RESET%

:: Проверка наличия WAD файла
if not exist "%WAD_FILE%" (
    echo %COLOR_RED%❌ Файл WAD (conquest.wad) не найден в папке проекта.%COLOR_RESET%
    pause
    exit /b
)

:: Проверка виртуального окружения
if not exist "%VENV_DIR%\" (
    echo %COLOR_YELLOW%🔧 Создание виртуального окружения...%COLOR_RESET%
    python -m venv %VENV_DIR%
)

:: Активация виртуального окружения
call %VENV_DIR%\Scripts\activate.bat

:: Проверка и установка зависимостей
echo %COLOR_YELLOW%🔧 Установка зависимостей...%COLOR_RESET%
pip install --upgrade pip >nul
pip install -r %REQUIREMENTS%

:: Выбор режима
echo %COLOR_MAGENTA%Выберите режим запуска:%COLOR_RESET%
echo 1) %COLOR_GREEN%Бот (ИИ играет)%COLOR_RESET%
echo 2) %COLOR_GREEN%Игрок (Вы управляете)%COLOR_RESET%
set /p mode_choice="Введите 1 или 2: "

if "%mode_choice%"=="1" (
    set MODE=bot
) else if "%mode_choice%"=="2" (
    set MODE=player
) else (
    echo %COLOR_RED%❌ Неверный выбор режима!%COLOR_RESET%
    pause
    exit /b
)

:: Запуск игры
echo %COLOR_CYAN%🚀 Запуск Doom II в режиме %MODE%...%COLOR_RESET%
python %PROJECT_DIR%\main.py --mode %MODE%

:: Завершение
deactivate
endlocal
pause
