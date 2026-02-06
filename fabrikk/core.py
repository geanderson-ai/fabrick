from fabrikk.context import ExecutionContext
from fabrikk.adapters.scheduler.apscheduling import APSchedulerAdapter
from fabrikk.logging_config import get_logger

logger = get_logger()

class Fabrick:
    def __init__(
        self,
        name: str,
        scheduler=None,
        start_at=None,
        retry=False,
        execution_mode="local",
        persistence=None,
        observability=None,
    ):
        self.name = name
        self.scheduler = scheduler
        self.start_at = start_at
        self.retry = retry
        self.execution_mode = execution_mode
        self.persistence = persistence
        self.observability = observability

        self.steps = {}
        self.start_step = None
        self.finish_step = None
        
        logger.info("Pipeline inicializado", name=self.name, mode=execution_mode)

    def start(self):
        logger.info("Iniciando pipeline", name=self.name)
        if not self.scheduler:
            logger.info("Executando pipeline imediatamente (sem scheduler)")
            self.run()
            return

        logger.info("Configurando scheduler", schedule=self.scheduler)
        adapter = APSchedulerAdapter()
        adapter.schedule(self)

    def register(self, *functions):
        for fn in functions:
            meta = getattr(fn, "__fabrikk__", None)
            if not meta:
                error_msg = f"{fn.__name__} não é um step Fabrikk"
                logger.error(error_msg)
                raise ValueError(error_msg)

            kind = meta["kind"]
            name = meta["name"]

            self.steps[name] = fn
            logger.debug("Step registrado", step=name, kind=kind)

            if kind == "start":
                self.start_step = fn
            elif kind == "finish":
                self.finish_step = fn

        if not self.start_step:
            error_msg = "Pipeline sem @start"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        if not self.finish_step:
            error_msg = "Pipeline sem @finish"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
            
        logger.info("Steps registrados com sucesso", count=len(self.steps))

    def run(self, input_data=None):
        logger.info("Execução iniciada", pipeline=self.name, input=input_data)
        ctx = ExecutionContext(input=input_data)
        current = self.start_step

        while True:
            step_name = getattr(current, "__fabrikk__", {}).get("name", current.__name__)
            logger.info("Executando step", step=step_name)
            
            try:
                result = current(ctx)
            except Exception as e:
                logger.exception("Exceção durante execução do step", step=step_name, error=str(e))
                raise

            status = result.get("status")
            next_state = result.get("next_state")
            
            logger.info("Step finalizado", step=step_name, status=status, next=next_state)

            if status != "success":
                error_msg = f"Erro no step {current.__name__}"
                logger.error(error_msg, result=result)
                if self.retry:
                    logger.warning("Retry ainda não implementado")
                    raise RuntimeError("Retry ainda não implementado")
                raise RuntimeError(error_msg)

            if current == self.finish_step:
                logger.info("Pipeline concluído com sucesso", result=result)
                return result

            if not next_state:
                error_msg = "next_state obrigatório"
                logger.error(error_msg, step=step_name)
                raise RuntimeError(error_msg)

            if next_state not in self.steps:
                error_msg = f"Próximo estado '{next_state}' não encontrado"
                logger.error(error_msg, current_step=step_name)
                raise RuntimeError(error_msg)

            current = self.steps[next_state]
