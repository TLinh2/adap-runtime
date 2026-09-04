from datetime import datetime
from pathlib import Path


class RuntimeTimingLogger:

    def __init__(self, filename="logs/timing/timing_log.csv"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
               
        path = Path(filename)
        path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.filename = (
            path.parent
            / f"{path.stem}_{timestamp}{path.suffix}"
        )

        self.file = open(
            self.filename,
            "a",
            buffering=8192
        )

        self.file.write(
            "task_id,"
            "t_log\n"
        )

    def log(
            self,
            task_id,
            t_log
    ):

        self.file.write(
            f"{task_id},"
            f"{t_log}\n"
        )

    def close(self):

        self.file.flush()
        self.file.close()