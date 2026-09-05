import csv
from pathlib import Path
from runtime.state.cluster_state import ClusterState
from datetime import datetime

class DecisionLogEntry:

        def __init__(
                self,
                timestamp,
                request_id: int,
                source_node_id: str,

                # unfinished_tasks: int,
                scheduler_name: str,
                selected_node_id: str,
                offloaded: bool,
                local_state: str,
                cluster_state: ClusterState,
        ):
                self.timestamp = timestamp
                self.request_id = request_id
                self.source_node_id = source_node_id

                # self.unfinished_tasks = unfinished_tasks
                self.scheduler_name = scheduler_name                                                                
                self.selected_node_id = selected_node_id
                self.offloaded = offloaded
                self.local_state = local_state
                self.cluster_state = cluster_state

        def to_dict(self):
               
               row = {
                      "timestamp": self.timestamp,
                      "request_id": self.request_id,
                      "source_node_id": self.source_node_id,

                #       "unfinished_tasks": self.unfinished_tasks,

                      "scheduler_name": self.scheduler_name,
                      "selected_node_id": self.selected_node_id,
                      "offloaded": self.offloaded,

                      "local_state": self.local_state,
                      "cluster_snapshot_time": self.cluster_state.cluster_snapshot_time
               }

               row.update(
                      self.cluster_state.to_dict()
               )

               return row

class CSVDecisionLogger():

        def __init__(
                self,
                filename="logs/decision/decision_log.csv"
        ):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                path = Path(filename)

                self.filename = (
                        path.parent
                        / f"{path.stem}_{timestamp}{path.suffix}"
                )


        def log(
                self,
                log_entry: DecisionLogEntry
        ):
                need_header = False

                if not Path(self.filename).exists():
                       need_header = True

                with open(
                        self.filename,
                        "a",
                        newline=""
                ) as f:

                        writer = csv.writer(f)
                        row = log_entry.to_dict()

                        if need_header:
                                writer.writerow(row.keys())

                        writer.writerow(row.values())