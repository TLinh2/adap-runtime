import os
import pandas as pd
import matplotlib.pyplot as plt

# ==========================
# CONFIG
# ==========================
CSV_FILE = "metrics-04_30_10.csv"

csv_name = os.path.splitext(CSV_FILE)[0]
PLOT_DIR = f"./plot/{csv_name}"

os.makedirs(PLOT_DIR, exist_ok=True)

# ==========================
# LOAD DATA
# ==========================
df = pd.read_csv(CSV_FILE)

# ==========================
# PLOT FUNCTION
# ==========================
def plot_metric_vs_request(df_node, metric, node_name):

    plt.figure(figsize=(10, 5))

    plt.plot(
        df_node["request_id"],
        df_node[metric],
        marker="o"
    )

    plt.xlabel("Request ID")
    plt.ylabel(metric.upper())
    plt.title(f"{node_name}: {metric.upper()} vs Request ID")
    plt.grid(True)

    plt.tight_layout()

    output_name = f"{node_name}_{metric}_request.png"
    save_path = os.path.join(PLOT_DIR, output_name)

    plt.savefig(save_path)
    plt.close()

    print(f"Saved: {save_path}")

# ==========================
# GENERATE PLOTS
# ==========================
metrics = [
    "cpu",
    "temp",
    "latency"
]

for node_name in df["node"].unique():

    df_node = (
        df[df["node"] == node_name]
        .sort_values("request_id")
    )

    for metric in metrics:
        plot_metric_vs_request(
            df_node,
            metric,
            node_name
        )

print("Done.")