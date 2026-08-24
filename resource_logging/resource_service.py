import threading
import time
from datetime import datetime
import psutil
from config import HOST_ID, SCHEDULER
from resource_logging.resource_logger import ResourceLogEntry, CSVResourceLogger

class ResourceLoggerService:

    def __init__(
        self,
        interval_sec: float,
        logger=None
    ):
        self.interval_sec = interval_sec

        self.logger = (
            logger
            if logger 
            else CSVResourceLogger()
        )

        self.running = False

        self. stop_event = threading.Event()

        self.thread = None

    def log_loop(self):
        while not self.stop_event.is_set():

            cpu_percent = psutil.cpu_percent()

            ram_percent = psutil.virtual_memory().percent

            temperature = psutil.sensors_temperatures()["cpu_thermal"][0].current

            entry = ResourceLogEntry(
                timestamp=datetime.now(),
                node_id=HOST_ID,
                scheduler=SCHEDULER,
                cpu_percent=cpu_percent,
                ram_percent=ram_percent,
                temperature=temperature,
            )

            self.logger.log(
                entry
            )
            time.sleep(self.interval_sec)

    def start(self):

        if self.running:
            return

        self.running = True

        self.stop_event.clear()

        self.logger = CSVResourceLogger()

        self.thread = threading.Thread(
            target=self.log_loop,
            daemon=True
        )

        self.thread.start()

        print("[ResourceLogger] Started")

    def stop(self):
        if not self.running:
            return
        self.running = False
        self.stop_event.set()

        self.thread.join()

        print("[ResourceLogger] Stopped")

    def schedule_start(
        self,
        execute_at
    ):
        delay = execute_at - time.time()

        if delay < 0:
            delay = 0

        threading.Timer(
            delay,
            self.start
        ).start()

        print(
            f"[ResourceLogger] "
            f"Scheduled start at "
            f"{execute_at}"
        )

    def schedule_stop(
        self,
        execute_at
    ):
        delay = execute_at - time.time()

        if delay < 0:
            delay = 0

        threading.Timer(
            delay,
            self.stop
        ).start()

        print(
            f"[ResourceLogger] "
            f"Scheduled stop at "
            f"{execute_at}"
        )