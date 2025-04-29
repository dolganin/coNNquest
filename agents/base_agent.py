class BaseAgent:
    def get_action(self, state):
        raise NotImplementedError("Each agent must implement the get_action method.")
