from agents.base_agent import BaseAgent
from models.adaptive_ensemble_agent import AdaptiveEnsembleAgent
import numpy as np

class BotAgent(BaseAgent):
    def __init__(self):
        self.agent = AdaptiveEnsembleAgent(
            stormtrooper_model_path="models/stormtrooper.onnx",
            pacifist_model_path="models/pacifist.onnx",
            balanced_model_path="models/balanced.onnx"
        )
        self.prev_health = None  # Для расчёта полученного урона

    def get_action(self, state):
        if not state:
            return [0] * 6

        game_vars = state.game_variables

        # Собираем нужные фичи для модели
        input_state = np.array([game_vars], dtype=np.float32)

        # Получаем индекс действия
        action_idx = self.agent.get_action(input_state)

        # Переводим индекс в OneHot вектор действий
        action = [0] * 6
        if 0 <= action_idx < len(action):
            action[action_idx] = 1

        # Логирование действий агента
        self._update_statistics(state)

        return action

    def _update_statistics(self, state):
        current_health = state.game_variables[0]  # Допустим, первое значение — здоровье
        moved_distance = 1.0  # Здесь можно подставить реальную метрику движения, если хочешь
        damage_taken = 0.0

        if self.prev_health is not None:
            damage_taken = max(0.0, self.prev_health - current_health)

        alive = current_health > 0

        self.agent.log_step(moved_distance, damage_taken, alive)

        if not alive:
            self.agent.log_death()

        self.prev_health = current_health
