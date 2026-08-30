import os
import time
import threading
import socket
import pickle
import numpy as np

from config import HOST_ID

# RUNTIME_URL = "http://127.0.0.1:9000/submit_task"
# WORKER_URL = "http://127.0.0.1:8000/submit_local"
# TIMEOUT = 30

RUNTIME_SOCKET = "/tmp/adap_runtime.sock"
WORKER_SOCKET = "/tmp/adap_worker.sock"


WINDOW_FOLDER = "./windows"



class TaskGenerator:

    def __init__(self):

        self.running = False

        self.mode = "RUNTIME"

        self.rate = 1.0

        self.send_interval = 1.0

        self.task_counter = 0

        self.total_sent = 0

        self.thread = None

        self.stop_event = threading.Event()
        self.socket = socket.socket(
            socket.AF_UNIX,
            socket.SOCK_DGRAM
        )

        self.window_files = self.load_window_files(
            WINDOW_FOLDER
        )
        self.windows = [
            np.load(
                os.path.join(
                    WINDOW_FOLDER,
                    filename
                )
            ).tolist()
            for filename in self.window_files
        ]

    def set_mode(self, mode):

        mode = mode.upper()

        if mode not in {
            "RUNTIME",
            "BASELINE"
        }:
            raise ValueError(
                f"Unknown experiment mode: {mode}"
            )

        self.mode = mode

    # =====================================
    # Utils
    # =====================================

    def load_window_files(self, folder):

        files = sorted(
            f for f in os.listdir(folder)
            if f.endswith(".npy")
        )

        if not files:
            raise ValueError(
                f"No .npy files found in {folder}"
            )

        return files

    def set_rate(self, rate):

        if rate <= 0:
            raise ValueError(
                "rate must be > 0"
            )

        self.rate = rate

        self.send_interval = 1.0 / rate

        print(
            f"[TaskGenerator] "
            f"Rate updated to "
            f"{rate} window/s"
        )

    # =====================================
    # Scheduled Commands
    # =====================================

    def schedule_start(
            self,
            rate,
            execute_at,
            mode="RUNTIME"
    ):

        def worker():

            delay = (
                execute_at
                - time.time()
            )

            if delay > 0:
                time.sleep(delay)

            self.set_mode(mode)

            self.set_rate(rate)

            if not self.running:
                self.start()

        threading.Thread(
            target=worker,
            daemon=True
        ).start()

    def schedule_stop(
        self,
        execute_at
    ):

        def worker():

            delay = (execute_at - time.time())

            if delay > 0:
                time.sleep(delay)

            if self.running:
                self.stop()

        threading.Thread(
            target=worker,
            daemon=True
        ).start()

    def schedule_rate_update(
            self,
            rate,
            execute_at
    ):

        def worker():

            delay = (
                execute_at
                - time.time()
            )

            if delay > 0:
                time.sleep(delay)

            self.set_rate(rate)

        threading.Thread(
            target=worker,
            daemon=True
        ).start()

    # =====================================
    # Send Task
    # =====================================

    def send_window(
            self,
            window
    ):

        self.task_counter += 1

        task_id = (
            f"{HOST_ID}_window_"
            f"{self.task_counter:08d}"
        )

        payload = {
            "task_id": task_id,
            "created_at": time.time(),
            "window": window,
            "source_node_id": HOST_ID
        }

        if self.mode == "BASELINE":

            socket_path = WORKER_SOCKET

        else:

            socket_path = RUNTIME_SOCKET

        try:

            
            message = pickle.dumps(
                payload,
                protocol=pickle.HIGHEST_PROTOCOL
            )

            self.socket.sendto(message, socket_path)

            self.total_sent += 1

            return True

        except OSError as e:

            print(
                f"[TaskGenerator] "
                f"Failed to send "
                f"{task_id}: {e}"
            )

            return False

    # =====================================
    # Generator Loop
    # =====================================

    def generator_loop(self):

        print(
            f"[TaskGenerator] Started "
            f"(rate={self.rate} window/s)"
        )

        file_index = 0

        while not self.stop_event.is_set():

            window = self.windows[
                file_index
            ]

            self.send_window(
                window
            )

            file_index = (
                file_index + 1
            ) % len(self.windows)

            time.sleep(
                self.send_interval
            )

        print(
            "[TaskGenerator] Stopped"
        )

    # =====================================
    # Lifecycle
    # =====================================

    def start(self):

        if self.running:
            return

        self.running = True

        self.stop_event.clear()

        self.thread = threading.Thread(
            target=self.generator_loop,
            daemon=True
        )

        self.thread.start()

    
    def stop(self):

        if not self.running:
            return

        self.running = False

        self.stop_event.set()

        if self.thread is not None:
            self.thread.join()

    # =====================================
    # Status
    # =====================================

    def get_status(self):

        return {
            "running": self.running,
            "rate": self.rate,
            "send_interval": self.send_interval,
            "total_sent": self.total_sent,
            "task_counter": self.task_counter
        }