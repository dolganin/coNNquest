from abc import ABC, abstractmethod

class BaseAgent(ABC):
    @abstractmethod
    def get_action(self, state):
        """Должен вернуть действие на основе состояния."""
        pass
