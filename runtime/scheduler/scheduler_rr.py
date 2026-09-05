from runtime.scheduler.scheduler_base import Scheduler
from runtime.state.scheduler_types import SchedulerInput, SchedulerOutput, Schedulers, DecisionReason

class RoundRobinScheduler(Scheduler):


    def __init__(self):
        self.current_index = 0
        self.name = Schedulers.ROUND_ROBIN
        super().__init__()

    def schedule(
            self,
            scheduler_input: SchedulerInput,
    ) -> SchedulerOutput:
        
        candidates = scheduler_input.candidates

        # Case 1: No neighbors
        if not candidates:
            return SchedulerOutput(
                selected_node=None,
                decision_reason=DecisionReason.ALL_NODES_BUSY
            )

        # Case 2: ROUND ROBIN
        selected_node = candidates [
            self.current_index % len(candidates)
        ]

        self.current_index = (
            self.current_index + 1
        ) % len(candidates)

        return SchedulerOutput(
            selected_node=selected_node,
            decision_reason=DecisionReason.ROUND_ROBIN
        )
        
        