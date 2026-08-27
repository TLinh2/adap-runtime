from runtime.scheduler.scheduler_base import Scheduler
from runtime.state.scheduler_types import SchedulerInput, SchedulerOutput, Schedulers, DecisionReason
from runtime.state.node_state import NodeState
from runtime.state.resource_state import ResourceState

class RoundRobinScheduler(Scheduler):


    def __init__(self):
        self.current_index = 0
        self.name = Schedulers.ROUND_ROBIN
        super().__init__()

    def schedule(
            self,
            scheduler_input: SchedulerInput,
    ) -> SchedulerOutput:
        
        host = scheduler_input.host
        candidates = scheduler_input.candidates

        should_offload = (
            host.cpu_state == ResourceState.CRITICAL
            and host.queue_size >= 10
        )

        # Case 1: Local
        if not should_offload:
            return SchedulerOutput(
                selected_node=host,
                offloaded=False,
                decision_reason=DecisionReason.LOCAL_HEALTHY
            )
        
        # Case 2: No neighbors
        if not candidates:

            return SchedulerOutput(
                selected_node=None,
                offloaded=False,
                decision_reason=DecisionReason.ALL_NODES_BUSY
            )

        # Case 3: ROUND ROBIN
        selected_node = candidates [
            self.current_index % len(candidates)
        ]

        self.current_index = (
            self.current_index + 1
        ) % len(candidates)

        return SchedulerOutput(
            selected_node=selected_node,
            offloaded=True,
            decision_reason=DecisionReason.ROUND_ROBIN
        )
        
        