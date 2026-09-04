import socket
import pickle
import threading
from queue import Queue, Empty

WORKER_SOCKET_PATH = "/tmp/adap_worker.sock"
OFFLOAD_PORT = 9300

class WorkerInterface:
    def __init__(self):
        self.local_queue = Queue()
        self.local_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.local_thread = None

        self.offload_queue = Queue()
        self.offload_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.offload_thread = None

        self.stop_event = threading.Event()
        

    def submit_local(
            self,
            selected_node_id: str,
            payload: dict
    ):

        self.local_queue.put((selected_node_id, payload))

        return {
            "accepted": True,
            "worker_id": str(selected_node_id),
        }

    def local_sender_loop(self):
        while not self.stop_event.is_set():
            try:
                (selected_node_id, payload) = self.local_queue.get(timeout=1)
            except Empty:
                continue

            try:
                message = pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL)
                self.local_socket.sendto(message, WORKER_SOCKET_PATH)

            except OSError as e:
                print(
                "[WorkerInterface] "
                f"Failed to dispatch local task "
                f"{payload.get('task_id', 'UNKNOWN')}: "
                f"{e}"
            )

            finally:
                self.local_queue.task_done()
        
    def forward_request(
            self,
            selected_node_id: str,
            payload: dict
    ):

        self.offload_queue.put((selected_node_id, payload))

        return {
            "accepted": True,
            "worker_id": str(selected_node_id),
        }

    def offload_sender_loop(self):
        while not self.stop_event.is_set():
            try:
                (selected_node_id, payload) = self.offload_queue.get(timeout=1)
            except Empty:
                continue

            try:
                message = pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL)
                target = (f"192.168.1.{selected_node_id}", OFFLOAD_PORT)
                self.offload_socket.sendto(message, target)

            except OSError as e:
                print(
                "[WorkerInterface] "
                f"Failed to offload task "
                f"to node "
                f"{selected_node_id}: {e}"
            )

            finally:

                self.offload_queue.task_done()

    def start(self):
        self.stop_event.clear()

        self.local_thread = threading.Thread(
            target=self.local_sender_loop,
            daemon=True
        )

        self.offload_thread = threading.Thread(
            target=self.offload_sender_loop,
            daemon=True
        )

        self.local_thread.start()
        self.offload_thread.start()

    def stop(self):
        self.stop_event.set()
        if self.local_thread is not None:
            self.local_thread.join()    
        if self.offload_thread is not None:
            self.offload_thread.join()

        self.local_socket.close()
        self.offload_socket.close()
