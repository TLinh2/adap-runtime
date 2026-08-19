from flask import Flask, request, jsonify
import numpy as np
import onnxruntime as ort
import time
import psutil
from worker.execution_logger import CSVExecutionLogger, ExecutionLogEntry

app = Flask(__name__)
logger = CSVExecutionLogger()


# -------------
# Loading model
# -------------

MODEL_PATH = "./onnx/bearing_cnn.onnx"
print("Loading model...")
session = ort.InferenceSession(
    MODEL_PATH,
    providers=["CPUExecutionProvider"]
)
input_name = session.get_inputs()[0].name
input_shape = session.get_inputs()[0].shape
print(input_shape)
print("Model loaded.")


@app.route("/infer", methods=["POST"])
def infer():
    arrival_time = time.time()

    data = request.get_json()


    if not data:
        return jsonify({"error": "No JSON"}), 400

    window = np.array(
        data["window"],
        dtype=np.float32
    )

    if window.ndim == 1:
        window = window[np.newaxis, :]

    if window.shape[1] != 1024:
        return jsonify({
            "error": f"Expected input shape (batch,1024), got {window.shape}"
        }), 400

    print("Worker ready.")
    print(f"Input shape: {window.shape}")
    print("Running inference...")


    infer_start_time = time.time()

    outputs = session.run(
        None,
        {input_name: window}
    )

    infer_end_time = time.time()

    predictions = np.argmax(outputs[0], axis=1)

    print("Inference completed.")


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


    return jsonify({
        "status": "success",
        "predictions": predictions.tolist(),
        "success": True
    }), 200



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
