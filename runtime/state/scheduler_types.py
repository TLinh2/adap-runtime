from runtime.state.cluster_state import ClusterState,NodeState

class DecisionReason:
    LOCAL_HEALTHY = "LOCAL_HEALTHY"
    ROUND_ROBIN = "ROUND_ROBIN"
    CPU_THRESHOLD = "CPU_THRESHOLD"
    RAM_THRESHOLD = "RAM_THRESHOLD"
    TEMPERATURE_THRESHOLD = "TEMPERATURE_THRESHOLD"
    LATENCY_THRESHOLD = "LATENCY_THRESHOLD"
    ALL_NODES_BUSY = "ALL_NODES_BUSY"
    NO_NODES_AROUND = "NO_NODES_AROUND"
    CAPACITY_AVAILABLE = "CAPACITY_AVAILABLE"

class Schedulers:
    ROUND_ROBIN = "ROUND_ROBIN"
    REACTIVE = "REACTIVE"
    PREDICTIVE = "PREDICTIVE"

class SchedulerInput:

    def __init__(
            self,
            request_id: int,
            host: NodeState,
            candidates: list[NodeState]
    ):
        self.request_id = request_id
        self.host = host
        self.candidates = candidates


class SchedulerOutput:

    def __init__(
            self,
            selected_node: NodeState,
            offloaded: bool,
            decision_reason: str
    ):
        self.selected_node = selected_node
        self.offloaded = offloaded
        self.decision_reason = decision_reason

    def __str__(self):
        return f"selected_node_id: {self.selected_node_id}, " \
                f"decision: {self.decision}"

