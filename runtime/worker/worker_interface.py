import requests
import socket
import pickle

WORKER_SOCKET_PATH = "/tmp/adap_worker.sock"

class WorkerInterface:
    def __init__(self):
        self.local_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

    def submit_local(
            self,
            selected_node_id: str,
            payload: dict
    ):

        try:
            
            message = pickle.dumps(payload, protocol=pcikle.HIGHEST_PROTOCOL)

            self.local_socket.sendto(message, WORKER_SOCKET_PATH)

            return {
                "accepted": True,
                "is_available": True,
                "worker_id": str(selected_node_id),
                "admission_status": "NOT_APPLICABLE",
                "admission_reason": "NOT_APPLICABLE",
            }
    
        except OSError as e:

            print(f"[WorkerInterface] Local inference failed: {e}")

            return {
                "accepted": False,
                "worker_id": None,
                "is_available": False,
                "admission_status": "NOT_APPLICABLE",
                "admission_reason": "NOT_APPLICABLE",
            }

    def check_admission(
        self,
        selected_node_id: str
    ):

        url = (
            f"http://192.168.1.{selected_node_id}:9000"
            f"/check_admission"
        )

        try:

            response = requests.get(
                url,
                timeout=5
            )
            response.raise_for_status()

            data = response.json()

            return {
                "accepted": data["accepted"],
                "is_available": data["is_available"],
                "worker_id": str(selected_node_id),
                "admission_reason": data["admission_reason"]
            }
        except requests.RequestException as e:

            print(
                f"[WorkerInterface] Admission check failed "
                f"for node{selected_node_id}: {e}"
            )

            return {
                "accepted" : False,
                "is_available": False,
                "worker_id": str(selected_node_id),
                "admission_reason": "NODE_UNREACHABLE"
            }
        
    def forward_request(
            self,
            selected_node_id: str,
            payload: dict
    ):

        # Ask admission of neighbor
        admission = self.check_admission(
            selected_node_id
        )

        # IF neighbor rejected
        if not admission["accepted"]:

            return {
                "accepted": False,
                "is_available": admission["is_available"],
                "worker_id": str(selected_node_id),
                "admission_status": "REJECTED",
                "admission_reason": admission["admission_reason"]
            }

        # IF neighbor agreed

        url = f"http://192.168.1.{selected_node_id}:9000/submit_task"

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=30
            )

            response.raise_for_status()

            data = response.json()

            return {
                "accepted": True,
                "is_available": admission["is_available"],
                "worker_id": str(selected_node_id),
                "admission_status": "ACCEPTED",
                "queue_size": data["queue_size"],
                "admission_reason": admission["admission_reason"]
            }

        except requests.RequestException as e:
            print(
                f"[WorkerInterface] Failed to forward request "
                f"to node {selected_node_id}: {e}"
            )

            return {
                "accepted": False,
                "is_available": False,
                "worker_id": str(selected_node_id),
                "admission_status": "FAILED",
                "admission_reason": "FORWARD_FAILED"
            }