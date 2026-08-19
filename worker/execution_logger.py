import csv
from pathlib import Path
from datetime import datetime

class ExecutionLogEntry:

    def __init__(
        self,
        task_id,
        t_wait,
        t_infer,
        t_total
    ):
        self.timestamp = datetime.now()

        self.task_id = task_id

        self.t_wait = t_wait

        self.t_infer = t_infer

        self.t_total = t_total

    def to_dict(self):

        return {

            "timestamp":
                self.timestamp,

            "task_id":
                self.task_id,

            "t_wait":
                self.t_wait,

            "t_infer":
                self.t_infer,

            "t_total":
                self.t_total
        }

class CSVExecutionLogger:

    def __init__(
        self,
        filename="logs/execution/execution_log.csv"
    ):
        self.filename = filename

        Path(
            self.filename
        ).parent.mkdir(
            parents=True,
            exist_ok=True
        )

    def log(
        self,
        log_entry: ExecutionLogEntry
    ):

        row = log_entry.to_dict()

        need_header = (
            not Path(
                self.filename
            ).exists()
        )

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