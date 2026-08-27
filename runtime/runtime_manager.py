from datetime import datetime
from queue import Queue
import threading
from queue import Empty
from runtime.state.scheduler_types import DecisionReason, SchedulerInput, SchedulerOutput
from runtime.logging.decision_logger import DecisionLogEntry
from config import HOST_ID

class RuntimeManager:

    def __init__(
            self,
            monitoring,
            scheduler,
            worker_interface,
            decision_logger,
    ):
        self.monitoring = monitoring
        self.scheduler = scheduler
        self.worker_interface = worker_interface
        self.decision_logger = decision_logger


        # FIFO queue chứa task
        self.task_queue = Queue()

        self.state_ready = threading.Event()

    def submit_task(self, payload):

        self.task_queue.put(payload)

        return {
            "status": "accepted",
            "queue_size": self.task_queue.qsize()
        }

    

    # =================
    # Background Thread
    # =================

    def scheduler_loop(self):

        while not self.stop_event.is_set():

            # Chờ tới khi có task
            try:
                task = self.task_queue.get(timeout=1)

            except Empty:
                continue

            try:
                self._process_task(task)

            except Exception as e:
                print(
                    "[RuntimeManager] "
                    f"Failed processing "
                    f"{task.get('task_id', 'UNKNOWN')}: "
                    f"{e}"
                )

            finally:
                self.task_queue.task_done()

    def _process_task(self, task):

        task_id = task["task_id"]
        source_node_id = task["source_node_id"]

        # Đọc cluster state mới nhất
        cluster_state = self.monitoring.cluster_state
        host = cluster_state.host

        # Filter available nodes
        candidates = cluster_state.get_available_neighbors()

        # Chạy thuật toán scheduler
        scheduler_input = SchedulerInput(
            request_id=task_id,
            host=cluster_state.host,
            candidates=candidates
        )

        scheduler_output = self.scheduler.schedule(
            scheduler_input
        )

        execution_result = self._execute_scheduler_output(
            task=task,
            scheduler_output=scheduler_output
        )        

        # ===========================
        # Lưu log
        # ===========================
        log_entry = DecisionLogEntry(
            timestamp=datetime.now(),
            request_id=task_id,
            source_node_id=source_node_id,

            queue_size=host.queue_size,
            unfinished_tasks=host.unfinished_tasks,
            
            scheduler_name=self.scheduler.name,

            selected_node_id=execution_result["selected_node_id"],
            is_available=execution_result["is_available"],
            offloaded=scheduler_output.offloaded,
            decision_reason=scheduler_output.decision_reason,

            admission_status=execution_result["admission_status"],
            admission_reason=execution_result["admission_reason"],

            local_state=host.overall_state,
            cluster_state=cluster_state
        )
        self.decision_logger.log(log_entry)

    def _execute_scheduler_output(
        self,
        task,
        scheduler_output
    ):

        selected_node = scheduler_output.selected_node

        # CASE 1
        # No node can execute this task

        if selected_node is None:
            return {
                "selected_node_id": None,
                "is_available": False,
                "admission_status": "NOT_EXECUTED",
                "admission_reason": "NO_AVAILABLE_NODE"
            }

            # FALLBACK/ ALERT

        # CASE 2
        # OFFLOAD (Đã lựa chọn ra node)
        selected_node_id = selected_node.node_id

        if scheduler_output.offloaded:

            task["source_node_id"] = HOST_ID
            
            response = self.worker_interface.forward_request(
                selected_node_id=selected_node_id,
                payload=task
            )

            if not response["is_available"]:
                scheduler_output.selected_node.is_available = False
                print(
                    f"[RuntimeManager] "
                    f"Node {selected_node_id} "
                    f"is currently not available"
                    f"Set node {selected_node_id} is_available = False"
                )

            return {
                "selected_node_id": selected_node_id,
                "is_available": response["is_available"],
                "admission_status": response["admission_status"],
                "admission_reason": response["admission_reason"]
            }


        # CASE 3
        # LOCAL            
        response = self.worker_interface.submit_local(
            selected_node_id=selected_node_id,
            payload=task
        )

        return {
            "selected_node_id": selected_node_id,
            "is_available": response["is_available"],
            "admission_status": "NOT_APPLICABLE",
            "admission_reason": "NOT_APPLICABLE"
        }
            
    def start(self):
        self.stop_event = threading.Event()

        self.monitoring.collect_cluster_state()

        self.state_ready.set()
        self.monitoring.start()


        self.scheduler_thread = threading.Thread(
            target=self.scheduler_loop
        )

        self.scheduler_thread.start()

    def stop(self):
        self.stop_event.set()
        self.scheduler_thread.join()
        self.monitoring.stop()
