from flask import Flask, request, jsonify

from runtime.monitoring.monitor import Monitoring
from runtime.scheduler.scheduler_rr import RoundRobinScheduler
from runtime.worker.worker_interface import WorkerInterface
from runtime.logging.decision_logger import CSVDecisionLogger
from runtime.runtime_manager import RuntimeManager
from runtime.state.cluster_state import ClusterState, NodeState
from runtime.state.resource_state import ResourceState
from config import SCHEDULER
from runtime.scheduler.scheduler_manager import create_scheduler
from runtime.state.scheduler_types import DecisionReason, AdmissionReason

class RuntimeServer:

    def __init__(self):

        self.app = Flask(__name__)

        workers = {
            "alice": NodeState(node_id="163"),
            "bob": NodeState(node_id="242"),
            "sinuhe": NodeState(node_id="50")
        }

        cluster_state = ClusterState(list(workers.values()))

        scheduler = create_scheduler(
            SCHEDULER
        )

        self.runtime_manager = RuntimeManager(
            monitoring=Monitoring(cluster_state),
            scheduler=scheduler,
            worker_interface=WorkerInterface(),
            decision_logger=CSVDecisionLogger(),
        )

        self.register_routes()

    def register_routes(self):

        @self.app.route(
            "/check_admission",
            methods=["GET"]
        )
        def check_admission():
            host = self.runtime_manager.monitoring.cluster_state.host

            # second check
            if host.overall_state == ResourceState.CRITICAL:
                return jsonify({
                "accepted": False,
                "admission_reason": AdmissionReason.NODE_CRITICAL,
                "is_available": False,
                "overall_state": host.overall_state,
            }), 200

            if host.overall_state == ResourceState.WARNING:
                return jsonify({
                "accepted": False,
                "admission_reason": AdmissionReason.NODE_WARNING,
                "is_available": False,
                "overall_state": host.overall_state,
            }), 200

            return jsonify({
                "accepted": True,
                "admission_reason": AdmissionReason.CAPACITY_AVAILABLE,
                "is_available": True,
                "overall_state": host.overall_state,
            }), 200


        @self.app.route("/submit_task", methods=["POST"])
        def submit_task():

            payload = request.json

            result = self.runtime_manager.submit_task(payload)

            return jsonify(result), 202

        @self.app.route("/metrics", methods=["GET"])
        def metrics():
            host = self.runtime_manager.monitoring.cluster_state.host
            if host.overall_state == ResourceState.HEALTHY:
                host.is_available = True
            else:
                host.is_available = False
            return jsonify({
                    "node_id": host.node_id,
                    "is_available": host.is_available,
                    "cpu_percent": host.cpu_percent,
                    "ram_percent": host.ram_percent,
                    "temperature": host.temperature,
                    "cpu_state": host.cpu_state,
                    "ram_state": host.ram_state,
                    "temperature_state": host.temperature_state,
                    "overall_state": host.overall_state,
                })

        

    def start(self):

        self.runtime_manager.start()

        try:

            self.app.run(
                host="0.0.0.0",
                port=9000
            )

        finally:

            self.runtime_manager.stop()


if __name__ == "__main__":

    server = RuntimeServer()

    server.start()