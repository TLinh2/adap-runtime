from flask import Flask, request, jsonify
import os
import socket
import pickle
import threading

from runtime.monitoring.monitor import Monitoring
from runtime.worker.worker_interface import WorkerInterface
from runtime.logging.decision_logger import CSVDecisionLogger
from runtime.logging.timing_logger import RuntimeTimingLogger
from runtime.runtime_manager import RuntimeManager
from runtime.state.cluster_state import ClusterState, NodeState
from config import SCHEDULER, MAX_WAIT_SECONDS
from runtime.scheduler.scheduler_manager import create_scheduler
from runtime.policy.offload_decision import OffloadDecision

RUNTIME_SOCKET_PATH = "/tmp/adap_runtime.sock"
OFFLOAD_PORT = 9300

class RuntimeServer:

    def __init__(self):

        self.app = Flask(__name__)

        # Socket 
        self.socket_stop_event = threading.Event()
        self.runtime_socket = None
        self.socket_thread = None

        self.offload_socket = None
        self.offload_thread = None

        workers = {
            "alice": NodeState(node_id="163"),
            "bob": NodeState(node_id="242"),
            "sinuhe": NodeState(node_id="50")
        }

        cluster_state = ClusterState(list(workers.values()))

        scheduler = create_scheduler(
            SCHEDULER
        )
        offload_decision = OffloadDecision(max_wait_seconds=MAX_WAIT_SECONDS)

        self.runtime_manager = RuntimeManager(
            monitoring=Monitoring(cluster_state),
            scheduler=scheduler,
            worker_interface=WorkerInterface(),
            offload_decision=offload_decision,
            decision_logger=CSVDecisionLogger(),
            timing_logger=RuntimeTimingLogger(),
        )

        self.register_routes()

    def register_routes(self):

        @self.app.route("/submit_task", methods=["POST"])
        def submit_task():

            payload = request.json

            result = self.runtime_manager.submit_task(payload)

            return jsonify(result), 202

        @self.app.route("/metrics", methods=["GET"])
        def metrics():
            host = self.runtime_manager.monitoring.cluster_state.host

            return jsonify({
                    "node_id": host.node_id,
                    "is_available": host.is_available,
                    "cpu_percent": host.cpu_percent,
                    "ram_percent": host.ram_percent,
                    "temperature": host.temperature,
                    "queue_size": host.queue_size,
                    "unfinished_tasks": host.unfinished_tasks,
                })

        @self.app.route("/runtime_status", methods=["GET"])
        def runtime_status():
            return jsonify({
                "queue_size": self.runtime_manager.task_queue.qsize(),
                "unfinished_tasks": self.runtime_manager.task_queue.unfinished_tasks,
                "local_queue": self.runtime_manager.worker_interface.local_queue.qsize(),
                "offload_queue": self.runtime_manager.worker_interface.offload_queue.qsize()
            }), 200

    def socket_listener(self):
        if os.path.exists(RUNTIME_SOCKET_PATH):
            os.remove(RUNTIME_SOCKET_PATH)
        self.runtime_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.runtime_socket.bind(RUNTIME_SOCKET_PATH)

        self.runtime_socket.settimeout(1.0)

        print(
            f"[RuntimeServer] "
            f"Listening on "
            f"{RUNTIME_SOCKET_PATH}"
        )

        while not self.socket_stop_event.is_set():
            try:

                message = self.runtime_socket.recv(65535)
            
            except socket.timeout:
                continue

            except OSError:
                break

            try:
                payload = pickle.loads(message)

                self.runtime_manager.submit_task(payload)
            except Exception as e:
                print(f"[RuntimeServer] Failed to received task: {e}")

    def start_socket_listener(self):
        self.socket_stop_event.clear()

        self.socket_thread = threading.Thread(
            target=self.socket_listener,
            daemon=True
        )
        self.offload_thread = threading.Thread(
            target=self.offload_listener,
            daemon=True
        )

        self.offload_thread.start()
        self.socket_thread.start()

    def stop_socket_listener(self):
        self.socket_stop_event.set()
        if self.runtime_socket is not None:
            self.runtime_socket.close()
        if self.offload_socket is not None:
            self.offload_socket.close()

        if self.offload_thread is not None:
            self.offload_thread.join()

        if self.socket_thread is not None:
            self.socket_thread.join()

        if os.path.exists(RUNTIME_SOCKET_PATH):
            os.remove(RUNTIME_SOCKET_PATH)

    def offload_listener(self):
        self.offload_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.offload_socket.bind(("0.0.0.0", OFFLOAD_PORT))
        self.offload_socket.settimeout(1.0)

        print(
            f"[RuntimeServer] "
            f"Listening for offloaded tasks "
            f"on UDP port {OFFLOAD_PORT}"
        )

        while not self.socket_stop_event.is_set():

            try:
                message, address = (self.offload_socket.recvfrom(65535))
            except socket.timeout:
                continue

            except OSError:
                break
            try:
                payload = pickle.loads(message)
                self.runtime_manager.submit_task(payload)
            except Exception as e:
                print(
                    "[RuntimeServer] "
                    f"Failed receiving "
                    f"offloaded task: {e}"
                )

    def start(self):

        self.runtime_manager.start()
        self.start_socket_listener()

        try:

            self.app.run(
                host="0.0.0.0",
                port=9000
            )

        finally:
            self.stop_socket_listener()
            self.runtime_manager.stop()



if __name__ == "__main__":

    server = RuntimeServer()

    server.start()