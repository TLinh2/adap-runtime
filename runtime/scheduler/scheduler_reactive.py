from runtime.scheduler.scheduler_base import Scheduler
from runtime.state.scheduler_types import SchedulerInput, SchedulerOutput, Schedulers, DecisionReason

class ReactiveThresholdScheduler(Scheduler):
    def __init__(self):
        self.name = Schedulers.REACTIVE
        super().__init__()

    def schedule(
            self,
            scheduler_input: SchedulerInput
    ) -> SchedulerOutput:
        candidates = self.filter_nodes(
            scheduler_input.cluster_state.nodes
        )

        best_node = self.select_best_node(
            candidates
        )

        return SchedulerOutput(
            selected_node_id=best_node.node_id,
            decision="reactive_threshold"
        )

class ThresholdConfig:

    def __init__(
            self,
            max_cpu_percent=80,
            max_ram_percent=90,
            max_temperature=70,
    ):
        self.max_cpu_percent = max_cpu_percent
        self.max_ram_percent = max_ram_percent
        self.max_temperature = max_temperature
        