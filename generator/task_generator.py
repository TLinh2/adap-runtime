import os
import time
import requests
import numpy as np
from config import HOST_ID

# ==========================
# CONFIG
# ==========================

MASTER_URL = "http://127.0.0.1:9000/submit_task"

SOURCE_NODE_ID = HOST_ID

WINDOW_FOLDER = "./windows"

SEND_INTERVAL = 0.1      # 100 ms

LOOP_FOREVER = True

TIMEOUT = 30

# ==========================


def load_window_files(folder):
    files = sorted(
        f for f in os.listdir(folder)
        if f.endswith(".npy")
    )
    return files


def send_window(filepath, filename, task_counter):

    data = np.load(filepath)

    # window_id = filename.replace(".npy", "")

    task_id = f"{SOURCE_NODE_ID}_window{task_counter:08d}"

    payload = {
        "task_id": task_id,
        "window": data.tolist(),
        "source_node_id": SOURCE_NODE_ID
    }

    try:
        response = requests.post(
            MASTER_URL,
            json=payload,
            timeout=TIMEOUT
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as e:
        print(
            f"[TaskGenerator] Failed to send "
            f"{task_id}: {e}"
        )

        return None


def main():

    files = load_window_files(WINDOW_FOLDER)

    print(f"Loaded {len(files)} windows")

    task_counter = 0

    while True:

        for filename in files:

            filepath = os.path.join(
                WINDOW_FOLDER,
                filename
            )

            task_counter += 1

            send_window(filepath, filename, task_counter)

            time.sleep(SEND_INTERVAL)

        if not LOOP_FOREVER:
            break

    print("Generator finished.")


if __name__ == "__main__":
    main()