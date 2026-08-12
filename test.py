import threading
import time
from runtime.monitoring.monitor import Monitoring
from runtime.scheduler.scheduler_rr import RoundRobinScheduler
from runtime.worker.worker_interface import WorkerInterface
from runtime.logging.decision_logger import ConsoleLogger, CSVDecisionLogger
from runtime.runtime_manager import RuntimeManager
from runtime.state.cluster_state import ClusterState, NodeState

workers = {
    # "alice": NodeState(node_id=str(163)),
    # "bob": NodeState(node_id=str(242)),
    "sinuhe": NodeState(node_id=str(50))
}
cluster1 = ClusterState(list(workers.values()))

runtime_manager = RuntimeManager(
    monitoring=Monitoring(cluster1),
    scheduler=RoundRobinScheduler(),
    worker_interface=WorkerInterface(),
    logger=CSVDecisionLogger(),
    cluster=cluster1
)

runtime_manager.start()

try: 
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    runtime_manager.stop()

# for i in range(10000):
#     response = runtime.handle_request(
#         request_id=i+1,
#         payload={"input_path": "windows/window_00001.npy"},
#         cluster=cluster1,
#     )

# print(response)
