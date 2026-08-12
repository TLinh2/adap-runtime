from runtime.state.scheduler_types import SchedulerInput, SchedulerOutput

class Scheduler():
    def schedule(
            self,
            scheduler_input: SchedulerInput
    ) -> SchedulerOutput:
        raise NotImplementedError 
        