# ConNquestEnv: Обертка над VizDoom с поддержкой обучения по волнам

## Описание

`ConNquestEnv` — это Python-класс обертки над движком VizDoom, предназначенный для пошагового обучения агентов с нуля в боевых условиях. Используется собственная WAD-карта (`ConNquest.wad`), где агент начинает в безопасной яме и сражается с постепенно усложняющимися волнами врагов. Поддерживается масштабируемое добавление врагов, оружия, предметов, а также автоматическая проверка на проходимость волны.

## Возможности

- Генерация волн на основе конфигурации
- Прогрессивное добавление врагов и предметов
- Проверка достаточности ресурсов перед волной
- Гибкая настройка через YAML
- Поддержка встроенных наград VizDoom (`living_reward`, `death_penalty`)
- Интеграция с Gym-подобным API: `step(obs) -> (obs, reward, done, info)`
- Поддержка `MAP01` и других карт через параметр
- Выходной `info`-словарь с внутренним состоянием (номер волны, убийства, здоровье и т.д.)

## Скриншоты карты

| Превью |     |     |
|--------|-----|-----|
| ![screen1](images/screen1.png) | ![screen2](images/screen2.png) | ![screen3](images/screen3.png) |
| ![screen4](images/screen4.png) | ![screen5](images/screen5.png) |     |

## Структура проекта

```
project/
├── env.py                 # Основной класс ConNquestEnv
├── config.yaml            # Конфигурационный YAML
├── ConNquest.wad          # Кастомная карта
├── images/
│   ├── screen1.png
│   ├── screen2.png
│   ├── screen3.png
│   ├── screen4.png
│   └── screen5.png
```

## Использование

```python
from env import ConNquestEnv

env = ConNquestEnv("config.yaml")
obs = env.reset()

done = False
while not done:
    action = env.game.get_available_buttons_size() * [0]  # пример: все кнопки = 0
    obs, reward, done, info = env.step(action)
```

## Зависимости

- Python 3.8+
- [ViZDoom](https://github.com/mwydmuch/ViZDoom)
- PyYAML

## Примечание

Всю логику конфигурации карты, врагов, волн, предметов и параметров VizDoom можно изменить через `config.yaml`.