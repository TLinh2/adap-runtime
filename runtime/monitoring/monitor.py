import threading
import time
import requests
from datetime import datetime
import psutil
from flask import jsonify

from runtime.state.cluster_state import ClusterState
from runtime.state.resource_state import ResourceState

class Monitoring:
    def __init__(
            self,
            cluster_state: ClusterState,
            interval: int = 1,
    ):
        self.cluster_state = cluster_state
        self.interval = interval

        self.stop_event = threading.Event()
        self.monitor_thread = None

    def collect_host_state(self):
        host = self.cluster_state.host

        cpu_percent = psutil.cpu_percent(interval=None)
        ram_percent = psutil.virtual_memory().percent
        temperature = psutil.sensors_temperatures()['cpu_thermal'][0].current
        queue_data = requests.get(
            f"http://192.168.1.{host.node_id}:8000/status",
            timeout=3
        ).json()
        queue_size = queue_data["queue_size"]

        host.update(
            cpu_percent=cpu_percent,
            ram_percent=ram_percent,
            temperature=temperature,
            queue_size=queue_size
        )

        host.update_health_state()

        if host.overall_state == ResourceState.HEALTHY:
            host.is_available = True
        else:
            host.is_available = False
    def collect_neighbors_state(self):
        for node in self.cluster_state.neighbors:
        
            try:

                metrics = requests.get(
                    f"http://192.168.1.{node.node_id}:9000/metrics",
                    timeout=3
                ).json()

                node.update(
                    is_available=metrics["is_available"],
                    cpu_percent=metrics["cpu_percent"],
                    ram_percent=metrics["ram_percent"],
                    temperature=metrics["temperature"],
                    queue_size=metrics["queue_size"]
                )

                node.update_health_state()

            except Exception as e:
                print(
                    f"[Monitoring]: Failed to collect metrics "
                    f"from node {node.node_id}: {e}"
                )

    # Update cluster state
    def collect_cluster_state(self):
        self.collect_host_state()
        self.collect_neighbors_state()
        
        self.cluster_state.cluster_snapshot_time = datetime.now()

    # Background thread
    def monitoring_loop(self):
        while not self.stop_event.is_set():
            self.collect_cluster_state()

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

