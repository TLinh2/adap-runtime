import threading
import time
from datetime import datetime
import psutil
from config import HOST_ID, SCHEDULER
from resource_logging.resource_logger import ResourceLogEntry, CSVResourceLogger

class ResourceLoggerService:

    def __init__(
        self,
        interval_sec: 1,
        logger=None
    ):
        self.interval_sec = interval_sec

        self.logger = (
            logger
            if logger 
            else CSVResourceLogger()
        )

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
        self.stop_event = threading.Event()

        self.thread = threading.Thread(
            target=self.log_loop,
            daemon=True
        )

        self.thread.start()

    def stop(self):
        self.stop_event.set()

        self.thread.join()