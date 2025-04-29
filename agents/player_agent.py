from agents.base_agent import BaseAgent

class PlayerAgent(BaseAgent):
    def get_action(self, state):
        # В режиме игрока — действия обрабатываются руками, ИИ не мешает
        return [0] * 6
