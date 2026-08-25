from runtime.state.node_state import NodeState
from runtime.state.resource_state import ResourceState
from config import HOST_ID

class ClusterState:
    def __init__(
            self, 
            nodes: list[NodeState], 
            cluster_snapshot_time=None
        ):
        self.nodes = nodes
        self.cluster_snapshot_time = cluster_snapshot_time
        self.host = None
        self.neighbors = []

        self._refresh_topology()

    def _refresh_topology(self):
        self.host = self.get_host_node(HOST_ID)
        self.neighbors = self.get_neighbor_nodes(HOST_ID)

    def get_host_node(self, host_node_id) -> NodeState | None:
        return self.get_node(host_node_id)
    
    def get_neighbor_nodes(self, host_node_id) -> list[NodeState]:
        return [
            node 
            for node in self.nodes
            if node.node_id != host_node_id
        ]

    def get_available_neighbors(self):
        return [node for node in self.neighbors if (node.is_available and node.overall_state == ResourceState.HEALTHY)]

    def add_node(self, node_state: NodeState):
        self.nodes.append(node_state)

    def get_node(self, node_id: str) -> NodeState | None:
        for node in self.nodes:
            if node.node_id == node_id:
                return node
        return None

    def get_average_cpu(self) -> float:
        if not self.nodes:
            return 0.0

        return (
            sum(node.cpu for node in self.nodes)
            / len(self.nodes)
        )

    def get_hottest_node(self) -> NodeState | None:
        if not self.nodes:
            return None

        return max(
            self.nodes,
            key=lambda n: n.temp
        )

    def get_least_loaded_node(self) -> NodeState | None:
        if not self.nodes:
            return None

        return min(
            self.nodes,
            key=lambda n: n.active_requests
        )

    def __str__(self):
        return "\n".join(
            str(node)
            for node in self.nodes
        )
    
    def to_dict(self):
        
        data = {}

        for node in self.nodes:

            prefix = f"node_{node.node_id}"

            data[f"{prefix}_cpu_percent"] = node.cpu_percent
            data[f"{prefix}_ram_percent"] = node.ram_percent
            # data[f"{prefix}_latency_ms"] = node.latency_ms
            data[f"{prefix}_temperature"] = node.temperature

        return data
