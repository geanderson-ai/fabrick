"""Fabrikk constants and sentinel values."""

# Sentinel toggles for pipeline configuration
ON = True
OFF = False

# Default states
STATE_IDLE = "idle"
STATE_FAILED = "failed"
STATE_COMPLETED = "completed"

# Step types
STEP_START = "start"
STEP_MIDDLE = "step"
STEP_FINISH = "finish"

# Execution modes
EXECUTION_LOCAL = "local"
EXECUTION_BACKGROUND = "background"
EXECUTION_QUEUE = "queue"
EXECUTION_CLOUD = "cloud"

# Persistence backends
PERSISTENCE_SQLITE = "sqlite"
PERSISTENCE_POSTGRES = "postgres"
PERSISTENCE_REDIS = "redis"

# Observability backends
OBSERVABILITY_LANGSMITH = "langsmith"
OBSERVABILITY_NONE = "none"

# Machine modes
MACHINE_FLEXIBLE = "flexible"
MACHINE_STRICT = "strict"
