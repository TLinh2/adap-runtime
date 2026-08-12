import psutil
import time

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
        self.latency_ms = None
        
    def update(self, cpu_percent, ram_percent, temperature, latency_ms=None):
        self.cpu_percent = cpu_percent
        self.ram_percent = ram_percent
        self.temperature = temperature
        self.latency_ms = latency_ms
    
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