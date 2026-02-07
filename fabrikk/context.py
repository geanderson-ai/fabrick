class ExecutionContext:
    def __init__(self, input=None, state=None, metadata=None):
        self.input = input
        self.state = state
        self.metadata = metadata or {}
        self.state_history = []
