import logging
import sys
import structlog

def configure_logging(log_level=logging.INFO):
    """
    Configura o sistema de logging para usar structlog com saída formatada.
    """
    
    # Processadores comuns para ambos os ambientes
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
    ]

    if sys.stderr.isatty():
        # Processadores específicos para desenvolvimento (saída colorida e legível)
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(),
        ]
    else:
        # Processadores para produção (JSON estruturado)
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

def get_logger(name=None):
    return structlog.get_logger(name)
