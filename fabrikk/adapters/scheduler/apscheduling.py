from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger

from fabrikk.adapters.scheduler.base import SchedulerAdapter
from fabrikk.logging_config import get_logger

logger = get_logger()

class APSchedulerAdapter(SchedulerAdapter):
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        logger.debug("BackgroundScheduler inicializado")

    def schedule(self, workflow):
        trigger = self._build_trigger(workflow)
        
        logger.info("Agendando job", job=workflow.name, trigger=str(trigger))

        self.scheduler.add_job(
            func=workflow.run,
            trigger=trigger,
            id=workflow.name,
            replace_existing=True
        )

        self.scheduler.start()
        logger.info("Scheduler iniciado")

    def _build_trigger(self, workflow):
        schedule = workflow.scheduler

        if isinstance(schedule, str):
            logger.debug("Criando CronTrigger", schedule=schedule)
            return CronTrigger.from_crontab(schedule)

        if isinstance(schedule, dict):
            kind = schedule.get("type")
            
            logger.debug("Criando trigger complexo", type=kind, value=schedule.get("value"))

            if kind == "interval":
                return IntervalTrigger(**schedule["value"])

            if kind == "date":
                return DateTrigger(**schedule["value"])

        error_msg = f"Scheduler inválido: {schedule}"
        logger.error(error_msg)
        raise ValueError(error_msg)
