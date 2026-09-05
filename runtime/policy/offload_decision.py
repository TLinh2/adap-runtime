import time


LOCAL = "LOCAL"
OFFLOAD = "OFFLOAD"


class OffloadDecision:

    def __init__(
        self,
        max_wait_seconds,
    ):
        self.max_wait_seconds = max_wait_seconds
        self.bootstrap_in_progress = False

    def decide(
        self,
        task,
        host,
        local_queue_size
    ):

        avg_service_time = host.avg_service_time

        # Bootstrap
        if avg_service_time is None:

            if not self.bootstrap_in_progress:

                self.bootstrap_in_progress = True

                return LOCAL

            return OFFLOAD

        # Service time đã có
        self.bootstrap_in_progress = False

        elapsed_wait = (time.time() - task["created_at"])
        worker_backlog = (host.unfinished_tasks 
                          if host.unfinished_tasks is not None 
                          else 0)
        
        total_local_backlog = (local_queue_size + worker_backlog)
        estimated_remaining_wait = (total_local_backlog * avg_service_time)
        estimated_total_wait = (elapsed_wait + estimated_remaining_wait)

        if (estimated_total_wait > self.max_wait_seconds):
            return OFFLOAD
        return LOCAL