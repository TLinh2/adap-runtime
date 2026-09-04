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
                queue_size: int,

                t_scheduler: float,
                # t_local_dispatch: float,
                # t_offload: float,
                t_execution: float,

                # unfinished_tasks: int,
                scheduler_name: str,
                selected_node_id: str,
                offloaded: bool,
                decision_reason: str,
                local_state: str,
                cluster_state: ClusterState,
        ):
                self.timestamp = timestamp
                self.request_id = request_id
                self.source_node_id = source_node_id
                self.queue_size = queue_size

                self.t_scheduler = t_scheduler
                # self.t_local_dispatch = t_local_dispatch
                # self.t_offload = t_offload
                self.t_execution = t_execution


                # self.unfinished_tasks = unfinished_tasks
                self.scheduler_name = scheduler_name                                                                
                self.selected_node_id = selected_node_id
                self.offloaded = offloaded
                self.decision_reason = decision_reason
                self.local_state = local_state
                self.cluster_state = cluster_state

        def to_dict(self):
               
               row = {
                      "timestamp": self.timestamp,
                      "request_id": self.request_id,
                      "source_node_id": self.source_node_id,
                      "queue_size": self.queue_size,

                #       "unfinished_tasks": self.unfinished_tasks,
                        "t_scheduler": self.t_scheduler,
                        # "t_local_dispatch": self.t_local_dispatch,
                        # "t_offload": self.t_offload,
                        "t_execution": self.t_execution,

                      "scheduler_name": self.scheduler_name,
                      "selected_node_id": self.selected_node_id,
                      "offloaded": self.offloaded,

                      "decision_reason": self.decision_reason,

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