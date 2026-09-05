import threading
import time
import requests
from datetime import datetime
import psutil
import socket
import json
from runtime.state.cluster_state import ClusterState
from runtime.state.resource_state import ResourceState

BROADCAST_ADDRESS = "192.168.1.255"
BROADCAST_PORT = 9400

BROADCAST_INTERVAL = 1.0
HEARTBEAT_TIMEOUT = 3.0

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

        # Broadcast
        self.broadcast_thread = None
        self.listener_thread = None
        self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.broadcast_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_BROADCAST,
            1
        )

        self.listener_socket = None
        self.sequence = 0
        self.neighbor_sequences = {
            node.node_id: -1
            for node in self.cluster_state.neighbors
        }
        self.neighbor_last_seen = {
            node.node_id: None
            for node in self.cluster_state.neighbors
        }
        self.last_accept_offload = None

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
        unfinished_tasks = queue_data["unfinished_tasks"]

        host.update(
            cpu_percent=cpu_percent,
            ram_percent=ram_percent,
            temperature=temperature,
            queue_size=queue_size,
            unfinished_tasks=unfinished_tasks
        )

        host.update_health_state()

        previous_accept_offload = self.last_accept_offload
        accept_offload = (host.overall_state == ResourceState.HEALTHY)
        host.is_available = accept_offload

        self.last_accept_offload = accept_offload
        if previous_accept_offload is not None and previous_accept_offload != accept_offload:
            self.broadcast_host_state(immediate=True)

    def broadcast_host_state(
        self,
        immediate=False
    ):
        host = self.cluster_state.host

        self.sequence += 1

        payload = {
            "node_id": host.node_id,
            "seq": self.sequence,
            "timestamp": time.time(),
            "cpu_percent": host.cpu_percent,
            "ram_percent": host.ram_percent,
            "temperature": host.temperature,

            "queue_size": host.queue_size,
            "unfinished_tasks": host.unfinished_tasks,

            "overall_state": host.overall_state,
            "accept_offload": host.is_available,
        }

        message = json.dumps(payload).encode("utf-8")
        try:
            self.broadcast_socket.sendto(
                message,
                (BROADCAST_ADDRESS, BROADCAST_PORT)
            )

        except OSError as e:
            print(
                "[Monitoring] "
                f"Broadcast failed: {e}"
            )

    def broadcast_loop(self):
        while not self.stop_event.is_set():
            self.broadcast_host_state()
            self.stop_event.wait(BROADCAST_INTERVAL)

    def broadcast_listener_loop(self):
        self.listener_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        self.listener_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )

        self.listener_socket.bind(("0.0.0.0", BROADCAST_PORT))
        self.listener_socket.settimeout(1.0)

        while not self.stop_event.is_set():
            try:
                message, address = (self.listener_socket.recvfrom(65535))
            except socket.timeout:
                continue
            except OSError:
                break

            try:
                payload = json.loads(message.decode("utf-8"))
                self.handle_broadcast(payload)

            except Exception as e:
                print(
                    "[Monitoring] "
                    f"Invalid broadcast: {e}"
                )
    def handle_broadcast(
        self,
        payload
    ):
        node_id = str(payload["node_id"])
        host = self.cluster_state.host

        if node_id == str(host.node_id):
            return
        node = next((node for node in self.cluster_state.neighbors if str(node.node_id) == node_id), None)
        if node is None:
            return

        seq = payload["seq"]

        previous_seq = self.neighbor_sequences[node_id]

        # Ignore duplicate
        if seq <= previous_seq:
            return
        
        self.neighbor_sequences[node_id] = seq
        self.neighbor_last_seen[node_id] = time.perf_counter()

        node.update(
            is_available=payload["accept_offload"],
            cpu_percent=payload["cpu_percent"],
            ram_percent=payload["ram_percent"],
            temperature=payload["temperature"],

            queue_size=payload["queue_size"],
            unfinished_tasks=payload["unfinished_tasks"]
        )
        node.update_health_state()

    def check_neighbor_timeouts(self):
        now = time.perf_counter()

        for node in self.cluster_state.neighbors:
            last_seen = self.neighbor_last_seen[node.node_id]
            if last_seen is None:
                continue

            elapsed = now - last_seen
            if elapsed > HEARTBEAT_TIMEOUT:
                node.is_available = False

    def collect_cluster_state(self):
        self.collect_host_state()
        self.check_neighbor_timeouts()
        self.cluster_state.cluster_snapshot_time = datetime.now()

    # Background thread
    def monitoring_loop(self):
        while not self.stop_event.is_set():
            self.collect_cluster_state()

            self.stop_event.wait(self.interval)

    def start(self):
        self.stop_event.clear()
        self.monitor_thread = threading.Thread(
            target=self.monitoring_loop,
            daemon=True
        )
        self.broadcast_thread = threading.Thread(
            target=self.broadcast_loop,
            daemon=True
        )
        self.listener_thread = threading.Thread(
            target=self.broadcast_listener_loop,
            daemon=True
        )

        self.monitor_thread.start()
        self.broadcast_thread.start()
        self.listener_thread.start()

    def stop(self):
        self.stop_event.set()

        if self.listener_socket is not None:
            self.listener_socket.join()

        if self.monitor_thread is not None:
            self.monitor_thread.join()

        if self.broadcast_thread is not None:
            self.broadcast_thread.join()

        if self.listener_thread is not None:
            self.listener_thread.join()

        self.broadcast_socket.close()
