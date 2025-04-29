import numpy as np
import logging
from agents.base_agent import BaseAgent
from models.adaptive_ensemble_agent import AdaptiveEnsembleAgent

class BotAgent(BaseAgent):
    def __init__(self):
        self.logger = logging.getLogger("BOT")
        self.agent = AdaptiveEnsembleAgent(
            stormtrooper_model_path="models/stormtrooper.onnx",
            pacifist_model_path="models/pacifist.onnx",
            balanced_model_path="models/balanced.onnx"
        )
        self.prev_health = None  # Для расчета полученного урона
        self.logger.info("[BOT] Агент успешно инициализирован.")

    def get_action(self, state):
        if state is None:
            self.logger.warning("[BOT] Получено пустое состояние. Возвращаем no-action.")
            return [0] * 6

        game_vars = state.game_variables
        if game_vars is None:
            self.logger.warning("[BOT] Нет переменных состояния игры. Возвращаем no-action.")
            return [0] * 6

        # Собираем фичи для подачи в модель
        input_state = np.array([game_vars], dtype=np.float32)

        action_idx = self.agent.get_action(input_state)

        action = [0] * 6
        if 0 <= action_idx < len(action):
            action[action_idx] = 1
        else:
            self.logger.warning(f"[BOT] Некорректный индекс действия: {action_idx}")

        # Логируем и обновляем статистику
        self._update_statistics(state)

        return action

    def _update_statistics(self, state):
        current_health = state.game_variables[0] if state.game_variables is not None else 100
        moved_distance = 1.0  # Можно поставить более сложную метрику движения
        damage_taken = 0.0

        if self.prev_health is not None:
            damage_taken = max(0.0, self.prev_health - current_health)

        alive = current_health > 0

        self.agent.log_step(moved_distance, damage_taken, alive)

        if not alive:
            self.logger.info("[BOT] Агент погиб. Логируем смерть.")
            self.agent.log_death()

        self.prev_health = current_health
