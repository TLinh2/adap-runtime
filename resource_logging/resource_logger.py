from datetime import datetime
import csv
from pathlib import Path

class ResourceLogEntry:

    def __init__(
        self,
        timestamp: datetime,
        node_id: str,
        scheduler: str,
        cpu_percent: float,
        ram_percent: float,
        temperature: float,
    ):
        self.timestamp = timestamp
        self.node_id = node_id
        self.scheduler = scheduler
        self.cpu_percent = cpu_percent
        self.ram_percent = ram_percent
        self.temperature = temperature

    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "node_id": self.node_id,
            "scheduler": self.scheduler,
            "cpu_percent": self.cpu_percent,
            "ram_percent": self.ram_percent,
            "temperature": self.temperature,
        }

class CSVResourceLogger:

    def __init__(
        self,
        filename="logs/resource/resource_log.csv"
    ):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        path = Path(filename)

        self.filename = (
            path.parent
            / f"{path.stem}_{timestamp}{path.suffix}"
        )

    def log(
        self,
        entry
    ):
        need_header = not Path(
            self.filename
        ).exists()

        row = entry.to_dict()

        with open(
            self.filename,
            "a",
            newline=""
        ) as f:

            writer = csv.writer(f)

            if need_header:
                writer.writerow(
                    row.keys()
                )

            writer.writerow(
                row.values()
            )