import psutil
import time
from runtime.state.resource_state import ResourceState

CPU_THRESHOLDS = {
    "warning_enter": 75,
    "warning_exit": 70,
    "critical_enter": 90,
    "critical_exit": 80,
}


RAM_THRESHOLDS = {
    "warning_enter": 75,
    "warning_exit": 70,
    "critical_enter": 90,
    "critical_exit": 85,
}


TEMP_THRESHOLDS = {
    "warning_enter": 65,
    "warning_exit": 60,
    "critical_enter": 75,
    "critical_exit": 70,
}


class NodeState:
    def __init__(
            self, 
            node_id: str,
    ):
        self.node_id = node_id
        self.is_available = True
        self.last_updated = time.perf_counter()
        self.cpu_percent = None
        self.ram_percent = None
        self.temperature = None
        
        self.avg_service_time = None

        self.cpu_state = ResourceState.HEALTHY
        self.ram_state = ResourceState.HEALTHY
        self.temperature_state = ResourceState.HEALTHY
        self.overall_state = ResourceState.HEALTHY

        self.queue_size = None
        self.unfinished_tasks = None

    def update(
            self, 
            is_available=True, 
            cpu_percent=None, 
            ram_percent=None, 
            temperature=None, 
            avg_service_time=None,
            queue_size=None,
            unfinished_tasks=None,
        ):

            self.is_available = is_available
            self.cpu_percent = cpu_percent
            self.ram_percent = ram_percent
            self.temperature = temperature
            self.avg_service_time = avg_service_time
            self.queue_size = queue_size
            self.unfinished_tasks = unfinished_tasks

    @staticmethod
    def update_resource_state(
            value,
            previous_state,
            warning_enter,
            warning_exit,
            critical_enter,
            critical_exit
        ):
    
            if previous_state == ResourceState.HEALTHY:
                if value >= critical_enter:
                    return ResourceState.CRITICAL
                if value >= warning_enter:
                    return ResourceState.WARNING
                return ResourceState.HEALTHY
    
            if previous_state == ResourceState.WARNING:
                if value >= critical_enter:
                    return ResourceState.CRITICAL
                if value < warning_exit:
                    return ResourceState.HEALTHY
                return ResourceState.WARNING


            if previous_state == ResourceState.CRITICAL:
                if value < warning_exit:
                    return ResourceState.HEALTHY
                if value < critical_exit:
                    return ResourceState.WARNING
                return ResourceState.CRITICAL
    
            return ResourceState.HEALTHY

    def update_health_state(self):
        self.cpu_state = self.update_resource_state(
            value=self.cpu_percent,
            previous_state=self.cpu_state,
            **CPU_THRESHOLDS
        )

        self.ram_state = self.update_resource_state(
            value=self.ram_percent,
            previous_state=self.ram_state,
            **RAM_THRESHOLDS
        )

        self.temperature_state = self.update_resource_state(
            value=self.temperature,
            previous_state=self.temperature_state,
            **TEMP_THRESHOLDS
        )        

        states = {
            self.ram_state,
            self.temperature_state
        }

        if ResourceState.CRITICAL in states:
            self.overall_state = (
                ResourceState.CRITICAL
            )

        elif ResourceState.WARNING in states:
            self.overall_state = (
                ResourceState.WARNING
            )

        else:

            self.overall_state = (
                ResourceState.HEALTHY
            )
    def __str__(self):
        return (
            f"NodeState(node_id={self.node_id}, "
            f"cpu_percent={self.cpu_percent}, "
            f"ram={self.ram_percent}, "
            f"temp={self.temperature}, "
            f"latency_ms={self.latency_ms}, "
            f"is_available={self.is_available}, "
            f"last_updated={self.last_updated}) "
        ) 