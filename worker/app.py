from flask import Flask, request, jsonify
import numpy as np
import onnxruntime as ort
import time
import psutil


app = Flask(__name__)



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

    start_time = time.perf_counter()

    outputs = session.run(
        None,
        {input_name: window}
    )

    end_time = time.perf_counter()
    latency_ms = (end_time - start_time) * 1000

    predictions = np.argmax(outputs[0], axis=1)

    print("Inference completed.")

    return jsonify({
        "status": "success",
        "predictions": predictions.tolist(),
        "latency_ms": latency_ms,
        "success": True
    }), 200

@app.route("/metrics", methods=["GET"])
def metrics():
    cpu_percent = psutil.cpu_percent(interval=None)

    ram_percent = psutil.virtual_memory().percent

    temperature = psutil.sensors_temperatures()['cpu_thermal'][0].current

    return jsonify({
        "node_id": 50,
        "cpu_percent": cpu_percent,
        "ram_percent": ram_percent,
        "temperature": temperature
    })



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
