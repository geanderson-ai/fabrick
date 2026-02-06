from abc import ABC, abstractmethod


class SchedulerAdapter(ABC):
    @abstractmethod
    def schedule(self, workflow):
        pass
