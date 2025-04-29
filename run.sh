#!/bin/bash

# Скрипт для запуска Doom II AI проекта с проверками и настройкой X-сервера (цветной)

# Цвета ANSI
COLOR_RESET="\033[0m"
COLOR_GREEN="\033[32m"
COLOR_YELLOW="\033[33m"
COLOR_RED="\033[31m"
COLOR_CYAN="\033[36m"
COLOR_MAGENTA="\033[35m"

PROJECT_DIR="."
VENV_DIR="venv"
CACHE_FILE=".requirements.hash"
WAD_FILE="$PROJECT_DIR/conquest.wad"

echo -e "${COLOR_CYAN}🛠 Проверка окружения VizDoom...${COLOR_RESET}"

# Проверяем наличие WAD файла
if [ ! -f "$WAD_FILE" ]; then
    echo -e "${COLOR_RED}❌ Файл WAD ($WAD_FILE) не найден. Поместите conquest.wad в папку проекта.${COLOR_RESET}"
    exit 1
fi

# Устанавливаем правильный DISPLAY для WSL
if [ -z "$DISPLAY" ]; then
    export DISPLAY=$(grep nameserver /etc/resolv.conf | awk '{print $2}'):0
    echo -e "${COLOR_GREEN}✅ Установлен DISPLAY: $DISPLAY${COLOR_RESET}"
else
    echo -e "${COLOR_GREEN}✅ DISPLAY уже задан: $DISPLAY${COLOR_RESET}"
fi

# Проверяем доступность X-сервера
if ! xdpyinfo >/dev/null 2>&1; then
    echo -e "${COLOR_RED}❌ X-сервер недоступен. Убедитесь, что VcXsrv запущен на Windows с параметрами:${COLOR_RESET}"
    echo "   - Disable access control"
    echo "   - Display number 0"
    echo "   - Без Native OpenGL"
    exit 1
else
    echo -e "${COLOR_GREEN}✅ X-сервер доступен.${COLOR_RESET}"
fi

# Проверяем виртуальное окружение
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${COLOR_YELLOW}🔧 Создание виртуального окружения...${COLOR_RESET}"
    python3 -m venv $VENV_DIR
fi

# Активируем виртуальное окружение
source $VENV_DIR/bin/activate

# Проверка кэша зависимостей
if [ -f "$CACHE_FILE" ]; then
    OLD_HASH=$(cat "$CACHE_FILE")
else
    OLD_HASH=""
fi

NEW_HASH=$(sha256sum "$PROJECT_DIR/requirements.txt" | awk '{print $1}')

if [ "$OLD_HASH" != "$NEW_HASH" ]; then
    echo -e "${COLOR_YELLOW}🔧 Изменения в requirements.txt обнаружены. Переустановка зависимостей...${COLOR_RESET}"
    pip install --upgrade pip
    pip install -r $PROJECT_DIR/requirements.txt
    echo "$NEW_HASH" > "$CACHE_FILE"
else
    echo -e "${COLOR_GREEN}✅ Requirements не изменились. Пропускаем установку зависимостей.${COLOR_RESET}"
fi

# Запрос режима запуска
echo -e "${COLOR_MAGENTA}Выберите режим запуска:${COLOR_RESET}"
echo -e "1) ${COLOR_GREEN}Бот (ИИ играет)${COLOR_RESET}"
echo -e "2) ${COLOR_GREEN}Игрок (Вы управляете)${COLOR_RESET}"
read -p "Введите 1 или 2: " mode_choice

if [ "$mode_choice" == "1" ]; then
    MODE="bot"
elif [ "$mode_choice" == "2" ]; then
    MODE="player"
else
    echo -e "${COLOR_RED}❌ Неверный выбор режима!${COLOR_RESET}"
    deactivate
    exit 1
fi

# Запуск игры
echo -e "${COLOR_CYAN}🚀 Запуск Doom II в режиме $MODE ...${COLOR_RESET}"
cd $PROJECT_DIR

# Устанавливаем нужный видеодрайвер для SDL
export SDL_VIDEODRIVER=x11

python3 main.py --mode $MODE

# Выход из виртуального окружения после завершения
deactivate
