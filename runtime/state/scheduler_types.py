from runtime.state.cluster_state import NodeState

class DecisionReason:
    LOCAL_UNDER_THRESHOLD = "LOCAL_UNDER_THRESHOLD"
    ROUND_ROBIN = "ROUND_ROBIN"
    ALL_NODES_BUSY = "ALL_NODES_BUSY"
    NO_NODES_AROUND = "NO_NODES_AROUND"
    LOWEST_PRESSURE = "LOWEST_PRESSURE"

class Schedulers:
    ROUND_ROBIN = "ROUND_ROBIN"
    REACTIVE = "REACTIVE"
    PREDICTIVE = "PREDICTIVE"

class SchedulerInput:

    def __init__(
            self,
            request_id: int,
            candidates: list[NodeState]
    ):
        self.request_id = request_id
        self.candidates = candidates


class SchedulerOutput:

    def __init__(
            self,
            selected_node: NodeState,
            decision_reason: str
    ):
        self.selected_node = selected_node
        self.decision_reason = decision_reason

    def __str__(self):

        selected_node_id = (
            self.selected_node.node_id
            if self.selected_node is not None
            else None
        )

        return (
            f"selected_node_id: "
            f"{selected_node_id}, "
            f"decision_reason: "
            f"{self.decision_reason}"
        )

