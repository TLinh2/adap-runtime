import os
import time
import threading
import requests
import numpy as np

from config import HOST_ID

MASTER_URL = "http://127.0.0.1:9000/submit_task"

WINDOW_FOLDER = "./windows"

TIMEOUT = 30


class TaskGenerator:

    def __init__(self):

        self.running = False

        self.rate = 1.0

        self.send_interval = 1.0

        self.task_counter = 0

        self.total_sent = 0

        self.thread = None

        self.stop_event = threading.Event()

        self.window_files = self.load_window_files(
            WINDOW_FOLDER
        )

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

            if not self.running:
                self.start()

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
            filepath,
            filename
    ):

        data = np.load(filepath)

        self.task_counter += 1

        task_id = (
            f"{HOST_ID}_window_"
            f"{self.task_counter:08d}"
        )

        payload = {
            "task_id": task_id,
            "created_at": time.time(),
            "window": data.tolist(),
            "source_node_id": HOST_ID
        }

        try:

            response = requests.post(
                MASTER_URL,
                json=payload,
                timeout=TIMEOUT
            )

            response.raise_for_status()

            self.total_sent += 1

            return response.json()

        except requests.RequestException as e:

            print(
                f"[TaskGenerator] "
                f"Failed to send "
                f"{task_id}: {e}"
            )

            return None

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

            filename = self.window_files[
                file_index
            ]

            filepath = os.path.join(
                WINDOW_FOLDER,
                filename
            )

            self.send_window(
                filepath,
                filename
            )

            file_index = (
                file_index + 1
            ) % len(self.window_files)

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