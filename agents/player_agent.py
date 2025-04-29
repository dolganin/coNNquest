import logging
from agents.base_agent import BaseAgent

class PlayerAgent(BaseAgent):
    def __init__(self):
        self.logger = logging.getLogger("PLAYER")
        self.logger.info("[PLAYER] Игрок успешно инициализирован.")

    def get_action(self, state):
        if state is None:
            self.logger.warning("[PLAYER] Пустое состояние получено. Возвращаем no-action.")
            return [0] * 6

        # Здесь игрок сам управляет, ИИ не вмешивается
        return [0] * 6
