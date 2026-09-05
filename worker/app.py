from flask import Flask, request, jsonify
import pickle
import socket
import os
import json
import threading
import time

from queue import Queue

import numpy as np
import onnxruntime as ort

from worker.execution_logger import (
    CSVExecutionLogger,
    ExecutionLogEntry
)

app = Flask(__name__)

logger = CSVExecutionLogger()

task_queue = Queue()

MODEL_PATH = "./onnx/bearing_cnn.onnx"
WORKER_SOCKET_PATH = "/tmp/adap_worker.sock"
WORKER_STATUS_SOCKET_PATH = "/tmp/adap_worker_status.sock"
print("[Worker] Loading model...")

session = ort.InferenceSession(
    MODEL_PATH,
    providers=[
        "CPUExecutionProvider"
    ]
)

input_name = session.get_inputs()[0].name

input_shape = session.get_inputs()[0].shape

print(f"[Worker] Input shape: "f"{input_shape}")
print("[Worker] Model loaded.")

def execute_inference(data):

    window = np.array(
        data["window"],
        dtype=np.float32
    )
    if window.ndim == 1:

        window = window[np.newaxis,:]

    if (window.ndim != 2 or window.shape[1] != 1024):

        raise ValueError(
            f"Expected input shape "
            f"(batch, 1024), "
            f"got {window.shape}"
        )

    infer_start_time = time.time()

    outputs = session.run(None, {input_name: window})

    infer_end_time = time.time()

    predictions = np.argmax(
        outputs[0],
        axis=1
    )
    t_wait = infer_start_time - data["created_at"]

    t_infer = infer_end_time - infer_start_time

    t_total = infer_end_time - data["created_at"]

    log_entry = ExecutionLogEntry(
        data["task_id"],
        t_wait,
        t_infer,
        t_total
    )

    logger.log(log_entry)

    # print(
    #     f"[Worker] Completed "
    #     f"{data['task_id']} | "
    #     f"wait={t_wait:.4f}s | "
    #     f"infer={t_infer:.4f}s | "
    #     f"total={t_total:.4f}s"
    # )

    return predictions

def inference_loop():

    print(
        "[Worker] "
        "Inference consumer started."
    )

    while True:

        # Blocks here until a task exists.
        data = task_queue.get()

        try:

            execute_inference(
                data
            )

        except Exception as e:

            print(
                f"[Worker] "
                f"Inference failed for "
                f"{data.get('task_id', 'UNKNOWN')}: "
                f"{e}"
            )

        finally:

            task_queue.task_done()

def enqueue_task(data):
    task_queue.put(data)
    return task_queue.qsize()

@app.route(
    "/submit_local",
    methods=["POST"]
)
def submit_local():

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({
            "error": "No JSON"
        }), 400

    required_fields = [
        "task_id",
        "created_at",
        "window"
    ]

    for field in required_fields:

        if field not in data:

            return jsonify({
                "error":
                    f"Missing {field}"
            }), 400

    queue_size = enqueue_task(data)

    # IMPORTANT:
    # Return immediately after enqueue.
    # Do NOT wait for inference.
    return jsonify({
        "status":
            "accepted",

        "task_id":
            data["task_id"],

        "queue_size":
            queue_size,

        "success":
            True
    }), 200


@app.route(
    "/status",
    methods=["GET"]
)
def status():

    return jsonify({
        "queue_size":
            task_queue.qsize(),

        "unfinished_tasks":
            task_queue.unfinished_tasks
    }), 200

def socket_listener():
    if os.path.exists(WORKER_SOCKET_PATH):
        os.remove(WORKER_SOCKET_PATH)

    worker_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    worker_socket.bind(WORKER_SOCKET_PATH)

    print(
        f"[Worker] "
        f"Listening on "
        f"{WORKER_SOCKET_PATH}"
    )

    while True:
        try:
            message = worker_socket.recv(65535)

            data = pickle.loads(message)

            queue_size = enqueue_task(data)

        except Exception as e:

            print(
                "[Worker] "
                f"Socket receive failed: {e}"
            )
def status_socket_listener():

    if os.path.exists(
        WORKER_STATUS_SOCKET_PATH
    ):
        os.remove(
            WORKER_STATUS_SOCKET_PATH
        )

    status_socket = socket.socket(
        socket.AF_UNIX,
        socket.SOCK_DGRAM
    )

    status_socket.bind(
        WORKER_STATUS_SOCKET_PATH
    )

    print(
        f"[Worker] "
        f"Status socket listening on "
        f"{WORKER_STATUS_SOCKET_PATH}"
    )

    while True:

        try:

            message, client_address = (
                status_socket.recvfrom(
                    4096
                )
            )

            request_data = json.loads(
                message.decode(
                    "utf-8"
                )
            )

            if (request_data.get("type")!= "STATUS_REQUEST"):
                continue

            response_data = {
                "queue_size":
                    task_queue.qsize(),

                "unfinished_tasks":
                    task_queue.unfinished_tasks
            }

            response = json.dumps(
                response_data
            ).encode(
                "utf-8"
            )

            status_socket.sendto(
                response,
                client_address
            )

        except Exception as e:

            print(
                "[Worker] "
                f"Status socket failed: {e}"
            )

# MAIN

if __name__ == "__main__":

    inference_thread = threading.Thread(
        target=inference_loop,
        daemon=True
    )

    inference_thread.start()
    socket_thread = threading.Thread(
        target=socket_listener,
        daemon=True
    )

    status_socket_thread = threading.Thread(
        target=status_socket_listener,
        daemon=True
    )

    status_socket_thread.start()

    socket_thread.start()

    app.run(
        host="0.0.0.0",
        port=8000,
        threaded=True
    )