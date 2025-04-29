import logging
import os
import sys
from vizdoom import DoomGame, FileDoesNotExistException

def initialize_game(mode):
    logger = logging.getLogger("INIT")
    game = DoomGame()

    config_path = f"configs/{mode}.cfg"

    if not os.path.exists(config_path):
        logger.critical(f"[INIT] Конфигурационный файл {config_path} не найден.")
        sys.exit(1)

    try:
        game.load_config(config_path)
        if mode == "bot":
            game.add_game_args("-host 1 -deathmatch +sv_spawnfarthest 1")
        game.set_window_visible(True)
        game.set_sound_enabled(True)
        game.init()
        logger.info(f"[INIT] Игра успешно инициализирована в режиме '{mode}'.")
    except FileDoesNotExistException as e:
        logger.critical(f"[INIT] Ошибка загрузки WAD файла: {e}")
        logger.critical("[INIT] Проверьте путь к WAD файлу в .cfg и его наличие в проекте.")
        sys.exit(1)
    
    return game
