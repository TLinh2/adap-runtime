import requests


class WorkerInterface:

    def infer_local(
            self,
            selected_node_id: str,
            payload: dict
    ):
        url = f"http://127.0.0.1:8000/infer"

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
                    "worker_id": str(selected_node_id),
                    "admission_status": "NOT_APPLICABLE",
                    "admission_reason": "NOT_APPLICABLE",
                    "predictions": data["predictions"],
                    "latency_ms": data["latency_ms"]
                }
    
        except requests.RequestException as e:

            print(f"[WorkerInterface] Local inference failed: {e}")

            return {
                "accepted": False,
                "worker_id": None,
                "admission_status": "NOT_APPLICABLE",
                "admission_reason": "NOT_APPLICABLE",
                "predictions": None,
                "latency_ms": None
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
                "worker_id": str(selected_node_id),
                "admission_status": "ACCEPTED",
                "queue_size": data["queue_size"],
                "admission_reason": data.get(
                    "admission_reason"
                )
            }

        except requests.RequestException as e:
            print(
                f"[WorkerInterface] Failed to forward request "
                f"to node {selected_node_id}: {e}"
            )

            return {
                "accepted": False,
                "worker_id": str(selected_node_id),
                "admission_status": "FAILED",
                "admission_reason": "FORWARD_FAILED"
            }