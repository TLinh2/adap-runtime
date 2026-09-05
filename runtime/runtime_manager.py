from datetime import datetime
from queue import Queue
import threading
from queue import Empty
import time
from runtime.state.scheduler_types import DecisionReason, SchedulerInput, SchedulerOutput
from runtime.logging.decision_logger import DecisionLogEntry
from config import HOST_ID
from runtime.state.resource_state import ResourceState

class RuntimeManager:

    def __init__(
            self,
            monitoring,
            scheduler,
            worker_interface,
            offload_decision,
            decision_logger,
            timing_logger,
    ):
        self.monitoring = monitoring
        self.scheduler = scheduler
        self.worker_interface = worker_interface
        self.offload_decision = offload_decision
        self.decision_logger = decision_logger
        self.timing_logger = timing_logger


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

    def runtime_loop(self):

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

    def _handle_fallback(
        self,
        task,
        reason
    ):
        # TODO:
        # implement fallback policy later

        print(
            "[RuntimeManager] "
            f"Fallback task "
            f"{task.get('task_id', 'UNKNOWN')} "
            f"reason={reason}"
        )

    def _process_task(self, task):

        task_id = task["task_id"]
        source_node_id = task["source_node_id"]

        # Đọc cluster state mới nhất
        cluster_state = self.monitoring.cluster_state
        host = cluster_state.host

        if host.overall_state == ResourceState.CRITICAL:
            self._handle_fallback(
                task=task,
                reason="HOST_CRITICAL"
            )
            return

        # is_remote_task = (str(source_node_id)!= str(HOST_ID))
        # if is_remote_task:

        #     self.worker_interface.submit_local(
        #         selected_node_id=host.node_id,
        #         payload=task
        #     )

        #     return

        decision = self.offload_decision.decide(
            task=task,
            host=host,
            local_queue_size=(self.worker_interface.local_queue.qsize())
        )

        if decision == "LOCAL":
            self.worker_interface.submit_local(selected_node_id=host.node_id, payload=task)
            selected_node_id = host.node_id
        if decision == "OFFLOAD":
            candidates = cluster_state.get_available_neighbors()
            scheduler_input = SchedulerInput(
                request_id=task_id,
                candidates=candidates
            )        

            scheduler_output = self.scheduler.schedule(
                scheduler_input
            )

            selected_node = scheduler_output.selected_node
            # CASE 1
            # No node can execute this task
            if selected_node is None:
                self._handle_fallback(task=task, reason="ALL_NODES_BUSY")
                return
    
            # CASE 2
            # OFFLOAD (Đã lựa chọn ra node)
            selected_node_id = selected_node.node_id

            # task["source_node_id"] = HOST_ID
            self.worker_interface.forward_request(
                selected_node_id=selected_node_id,
                payload=task
            )

        
        # ===========================
        # Lưu log
        # ===========================
        logging_started_at = time.perf_counter()

        log_entry = DecisionLogEntry(
            timestamp=datetime.now(),
            request_id=task_id,
            source_node_id=source_node_id,

            queue_size=host.queue_size,
            
            scheduler_name=self.scheduler.name,
            selected_node_id=selected_node_id,
            offloaded=decision,
            decision_reason=scheduler_output.decision_reason,

            local_state=host.overall_state,
            cluster_state=cluster_state
        )
        self.decision_logger.log(log_entry)

        logging_finished_at = time.perf_counter()
        t_log = logging_finished_at - logging_started_at

        self.timing_logger.log(task_id=task_id, t_log=t_log)
            
    def start(self):
        self.stop_event = threading.Event()

        self.monitoring.collect_cluster_state()
        self.worker_interface.start()

        self.state_ready.set()
        self.monitoring.start()


        self.runtime_thread = threading.Thread(
            target=self.runtime_loop
        )

        self.runtime_thread.start()

    def stop(self):
        self.stop_event.set()
        self.runtime_thread.join()
        self.worker_interface.stop()

        self.monitoring.stop()
        self.timing_logger.close()
