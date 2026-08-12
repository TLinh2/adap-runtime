from runtime.scheduler.scheduler_base import Scheduler
from runtime.state.scheduler_types import SchedulerInput, SchedulerOutput, Schedulers, DecisionReason
from runtime.state.node_state import NodeState
from config import CPU_THRESHOLD

class RoundRobinScheduler(Scheduler):


    def __init__(self):
        self.current_index = 0
        self.name = Schedulers.ROUND_ROBIN
        super().__init__()

    def schedule(
            self,
            scheduler_input: SchedulerInput,
    ) -> SchedulerOutput:
        
        cluster = scheduler_input.cluster_state
        host = cluster.host
        neighbors = cluster.neighbors

        # Case 1: Local
        if host.cpu_percent < CPU_THRESHOLD:
            return SchedulerOutput(
                selected_node_id=host.node_id,
                offloaded=False,
                decision_reason=DecisionReason.LOCAL_HEALTHY
            )
        
        # Case 2: No neighbors
        if not neighbors:

            return SchedulerOutput(
                selected_node_id=host.node_id,
                offloaded=False,
                decision_reason=DecisionReason.NO_NODES_AROUND
            )

        # Case 3: ROUND ROBIN
        selected_node = neighbors [
            self.current_index % len(neighbors)
        ]

        self.current_index = (
            self.current_index + 1
        ) % len(neighbors)

        return SchedulerOutput(
            selected_node_id=selected_node.node_id,
            offloaded=True,
            decision_reason=DecisionReason.ROUND_ROBIN
        )
        
        