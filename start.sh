#!/bin/bash
set -e

# Проверка существования .venv
if [ ! -d ".venv" ]; then
  echo "Виртуальное окружение не найдено, создаю .venv..."
  python3 -m venv .venv
else
  echo "Окружение .venv уже существует."
fi

echo "Активация виртуального окружения..."
source .venv/bin/activate

echo "Установка зависимостей с обходом PEP 668..."
pip3 install --upgrade pip --break-system-packages
pip3 install -r requirements.txt --break-system-packages

echo "Запуск main.py..."
python3 main.py

echo "Деактивация виртуального окружения..."
deactivate
