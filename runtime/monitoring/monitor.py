import threading
import time
import requests
from datetime import datetime

from runtime.state.cluster_state import ClusterState

class Monitoring:
    def __init__(
            self,
            cluster: ClusterState,
            interval: int = 5,
    ):
        self.cluster_state = cluster
        self.interval = interval

        self.stop_event = threading.Event()
        self.monitor_thread = None

    # Update cluster state
    def collect_cluster_state(self):

        for node in self.cluster_state.nodes:

            try:

                metrics = requests.get(
                    f"http://192.168.1.{node.node_id}:8000/metrics",
                    timeout=3
                ).json()

                node.update(
                    cpu_percent=metrics["cpu_percent"],
                    ram_percent=metrics["ram_percent"],
                    temperature=metrics["temperature"],
                )

            except Exception as e:
                print(
                    f"[Monitoring]: Failed to collect metrics "
                    f"from node {node.node_id}: {e}"
                )
        self.cluster_state.cluster_snapshot_time = datetime.now()

    # Background thread
    def monitoring_loop(self):
        while not self.stop_event.is_set():
            self .collect_cluster_state()

            time.sleep(self.interval)

    def start(self):
        self.monitor_thread = threading.Thread(
            target=self.monitoring_loop,
            daemon=True
        )

        self.monitor_thread.start()

    def stop(self):
        self.stop_event.set()

        if self.monitor_thread is not None:
            self.monitor_thread.join()
        