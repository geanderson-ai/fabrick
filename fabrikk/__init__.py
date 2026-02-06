from .core import Fabrick
from .decorators import start, step, finish
from .constants import ON, OFF
from .logging_config import configure_logging, get_logger

# Configura logging padrão ao importar
configure_logging()

__all__ = ["Fabrick", "start", "step", "finish", "ON", "OFF", "get_logger"]
