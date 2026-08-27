from runtime.scheduler.scheduler_base import Scheduler
from runtime.state.scheduler_types import SchedulerInput, SchedulerOutput, Schedulers, DecisionReason
from runtime.state.resource_state import ResourceState
class ReactiveThresholdScheduler(Scheduler):
    def __init__(self):
        self.name = Schedulers.REACTIVE
        super().__init__()

    def calculate_pressure(self, node):
        cpu_pressure = node.cpu_percent / 90

        ram_pressure = node.ram_percent / 90

        temp_pressure = node.temperature / 75

        return (cpu_pressure + ram_pressure + temp_pressure) / 3

    def schedule(
            self,
            scheduler_input: SchedulerInput
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

        # Case 3: REACTIVE
        selected_node = min(candidates, key=self.calculate_pressure)

        return SchedulerOutput(
            selected_node=selected_node,
            offloaded=True,
            decision_reason=DecisionReason.LOWEST_PRESSURE
        )
        