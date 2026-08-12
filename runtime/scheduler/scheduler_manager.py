from runtime.scheduler.scheduler_rr import RoundRobinScheduler
from runtime.scheduler.scheduler_reactive import ReactiveThresholdScheduler
# from runtime.scheduler.scheduler_predictive import PredictiveScheduler


SCHEDULERS = {
    "ROUND_ROBIN": RoundRobinScheduler,
    "REACTIVE": ReactiveThresholdScheduler,
    # "PREDICTIVE": PredictiveScheduler,
}


def create_scheduler(selected_scheduler: str):

    try:
        scheduler_class = SCHEDULERS[selected_scheduler]
    except KeyError:
        raise ValueError(
            f"Unknown scheduler version: {selected_scheduler}"
        )

    return scheduler_class()