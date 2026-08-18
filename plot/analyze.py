from pathlib import Path

import re
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

from config import HOST_ID
# ============================================================
# CONFIG
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DECISION_LOG_DIR = PROJECT_ROOT / "logs" / "decision"
RESOURCE_LOG_DIR = PROJECT_ROOT / "logs" / "resource"

OUTPUT_DIR = PROJECT_ROOT / "analyze" / "18-08"
PLOT_DIR = OUTPUT_DIR / "plots"
CSV_DIR = OUTPUT_DIR / "csv"


# ============================================================
# FILE DISCOVERY
# ============================================================

def find_latest_file(directory: Path, pattern: str) -> Path:
    """Return the newest CSV matching pattern."""
    files = list(directory.glob(pattern))

    if not files:
        raise FileNotFoundError(
            f"No files found in {directory} matching {pattern}"
        )

    return max(files, key=lambda p: p.stat().st_mtime)


def find_latest_decision_log() -> Path:
    return find_latest_file(
        DECISION_LOG_DIR,
        "decision_log*.csv"
    )


def find_latest_resource_log() -> Path:
    """
    Current setup:
    resource logger runs independently on each Pi and writes
    files under ./logs, e.g. resource_log_20260817_103332.csv.
    """
    return find_latest_file(
        RESOURCE_LOG_DIR,
        "resource_log*.csv"
    )


# ============================================================
# LOADING
# ============================================================

def load_logs():
    decision_path = find_latest_decision_log()
    resource_path = find_latest_resource_log()

    print(f"[Analyzer] Decision log : {decision_path}")
    print(f"[Analyzer] Resource log : {resource_path}")

    decision_df = pd.read_csv(decision_path)
    resource_df = pd.read_csv(resource_path)

    decision_df["timestamp"] = pd.to_datetime(
        decision_df["timestamp"]
    )
    resource_df["timestamp"] = pd.to_datetime(
        resource_df["timestamp"]
    )

    return decision_df, resource_df


# ============================================================
# HELPERS
# ============================================================

def save_csv(df: pd.DataFrame, filename: str):
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    path = CSV_DIR / filename
    df.to_csv(path, index=False)
    print(f"[Analyzer] Wrote {path}")


def save_plot(filename: str):
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    path = PLOT_DIR / filename
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"[Analyzer] Wrote {path}")


def numeric_series(df, column):
    if column not in df.columns:
        return None
    return pd.to_numeric(df[column], errors="coerce")


# ============================================================
# RESOURCE LOG PLOTS
# ============================================================

def plot_host_resources(resource_df: pd.DataFrame):
    """
    Plot host CPU, RAM and temperature from the independent
    resource logger.
    """

    resource_df = resource_df.sort_values("timestamp")

    # CPU
    plt.figure(figsize=(10, 5))
    plt.plot(
        resource_df["timestamp"],
        resource_df["cpu_percent"],
        label="CPU (%)"
    )
    plt.xlabel("Time")
    plt.ylabel("CPU (%)")
    plt.title(f"Host CPU over Time - Node {HOST_ID}")
    plt.grid(True, alpha=0.3)
    plt.legend()
    save_plot("host_cpu_over_time.png")

    # RAM
    plt.figure(figsize=(10, 5))
    plt.plot(
        resource_df["timestamp"],
        resource_df["ram_percent"],
        label="RAM (%)"
    )
    plt.xlabel("Time")
    plt.ylabel("RAM (%)")
    plt.title(f"Host RAM over Time - Node {HOST_ID}")
    plt.grid(True, alpha=0.3)
    plt.legend()
    save_plot("host_ram_over_time.png")

    # Temperature
    plt.figure(figsize=(10, 5))
    plt.plot(
        resource_df["timestamp"],
        resource_df["temperature"],
        label="Temperature (°C)"
    )
    plt.xlabel("Time")
    plt.ylabel("Temperature (°C)")
    plt.title(f"Host Temperature over Time - Node {HOST_ID}")
    plt.grid(True, alpha=0.3)
    plt.legend()
    save_plot("host_temperature_over_time.png")

    # Combined
    fig, axes = plt.subplots(
        3, 1,
        figsize=(11, 9),
        sharex=True
    )

    axes[0].plot(
        resource_df["timestamp"],
        resource_df["cpu_percent"]
    )
    axes[0].set_ylabel("CPU (%)")
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(
        resource_df["timestamp"],
        resource_df["ram_percent"]
    )
    axes[1].set_ylabel("RAM (%)")
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(
        resource_df["timestamp"],
        resource_df["temperature"]
    )
    axes[2].set_ylabel("Temp (°C)")
    axes[2].set_xlabel("Time")
    axes[2].grid(True, alpha=0.3)

    fig.suptitle(f"Host Resource Utilization - Node {HOST_ID}")

    save_plot("host_combined_resources.png")


# ============================================================
# DECISION LOG SNAPSHOT PLOTS
# ============================================================

def get_node_ids_from_decision_log(decision_df):
    """
    Discover node IDs from columns such as:
    node_50_cpu_percent
    node_163_ram_percent
    """
    node_ids = set()

    pattern = re.compile(r"^node_(.+?)_(cpu|ram|temperature)_")

    for column in decision_df.columns:
        match = pattern.match(column)

        if match:
            node_ids.add(match.group(1))

    return sorted(node_ids)


def plot_decision_node_resources(decision_df: pd.DataFrame):
    """
    Plot the resource snapshots that the scheduler actually saw.
    This includes the host and neighbor nodes.

    IMPORTANT:
    These are decision-time snapshots, NOT ground-truth resource
    measurements from the corresponding node.
    """

    node_ids = get_node_ids_from_decision_log(decision_df)

    if not node_ids:
        print("[Analyzer] No node resource snapshot columns found.")
        return

    decision_df = decision_df.sort_values("timestamp")

    for node_id in node_ids:

        metrics = [
            ("cpu_percent", "CPU (%)", "cpu"),
            ("ram_percent", "RAM (%)", "ram"),
            ("temperature", "Temperature (°C)", "temperature"),
        ]

        for suffix, ylabel, filename_suffix in metrics:

            column = f"node_{node_id}_{suffix}"

            if column not in decision_df.columns:
                continue

            values = pd.to_numeric(
                decision_df[column],
                errors="coerce"
            )

            plt.figure(figsize=(10, 5))
            plt.plot(
                decision_df["timestamp"],
                values,
                marker=".",
                markersize=2
            )

            plt.xlabel("Decision Time")
            plt.ylabel(ylabel)
            plt.title(
                f"Node {node_id} {ylabel} "
                f"(Scheduler Snapshot)"
            )
            plt.grid(True, alpha=0.3)

            save_plot(
                f"node_{node_id}_{filename_suffix}_snapshot.png"
            )


# ============================================================
# OFFLOAD ANALYSIS
# ============================================================

def analyze_offloads(decision_df: pd.DataFrame):
    offloaded_df = decision_df[
        decision_df["offloaded"] == True
    ].copy()

    save_csv(
        offloaded_df,
        "offloaded_requests.csv"
    )

    total_offloaded = len(offloaded_df)

    accepted = (
        offloaded_df["admission_status"]
        .astype(str)
        .str.upper()
        .eq("ACCEPTED")
        .sum()
    )

    rejected = (
        offloaded_df["admission_status"]
        .astype(str)
        .str.upper()
        .eq("REJECTED")
        .sum()
    )

    acceptance_rate = (
        accepted / total_offloaded * 100
        if total_offloaded
        else 0
    )

    rejection_rate = (
        rejected / total_offloaded * 100
        if total_offloaded
        else 0
    )

    return {
        "total_offloaded": total_offloaded,
        "offload_accepted": int(accepted),
        "offload_rejected": int(rejected),
        "offload_acceptance_rate": acceptance_rate,
        "offload_rejection_rate": rejection_rate,
    }


# ============================================================
# LOCAL INFERENCE ANALYSIS
# ============================================================

def analyze_local_inference(decision_df: pd.DataFrame):
    local_df = decision_df[
        decision_df["offloaded"] == False
    ].copy()

    save_csv(
        local_df,
        "infer_local_requests.csv"
    )

    return {
        "total_local_inference": len(local_df)
    }


# ============================================================
# REMOTE REQUEST ANALYSIS
# ============================================================

def analyze_remote_requests(decision_df: pd.DataFrame):
    """
    A request is considered remote if:
        source_node_id != selected_node_id

    For requests arriving at this runtime from another node:
        source_node_id != HOST_ID

    Then classify:
        - remote_local
        - remote_offloaded_again
        - remote_local_despite_host_below_threshold

    The last classification is intentionally based on the
    host snapshot available in the decision log. It is meant
    to identify the "out-of-date / inconsistent admission"
    situation discussed in the experiment design.
    """

    remote_received_df = decision_df[
        decision_df["source_node_id"].astype(str) != str(HOST_ID)
    ].copy()

    save_csv(
        remote_received_df,
        "remote_requests.csv"
    )

    remote_local = remote_received_df[
        remote_received_df["offloaded"] == False
    ].copy()

    remote_offloaded_again = remote_received_df[
        remote_received_df["offloaded"] == True
    ].copy()

    # Host CPU snapshot, if available.
    host_cpu_column = f"node_{HOST_ID}_cpu_percent"

    if host_cpu_column in remote_received_df.columns:

        host_cpu = pd.to_numeric(
            remote_received_df[host_cpu_column],
            errors="coerce"
        )

        # Current threshold is intentionally not hard-coded here.
        # This classification only records rows for which the
        # host CPU snapshot is available. The exact threshold
        # can be added later from config when the experiment
        # analysis is finalized.
        remote_below_threshold_df = remote_received_df[
            host_cpu.notna()
        ].copy()

        remote_below_threshold_df[
            "host_cpu_snapshot"
        ] = host_cpu.loc[
            remote_below_threshold_df.index
        ]

        save_csv(
            remote_below_threshold_df,
            "remote_requests_with_host_snapshot.csv"
        )

    else:
        remote_below_threshold_df = pd.DataFrame()

    save_csv(
        remote_local,
        "remote_infer_local_requests.csv"
    )

    save_csv(
        remote_offloaded_again,
        "remote_offloaded_again_requests.csv"
    )

    return {
        "remote_received": len(remote_received_df),
        "remote_infer_local": len(remote_local),
        "remote_offloaded_again": len(remote_offloaded_again),
        "remote_with_host_snapshot": len(
            remote_below_threshold_df
        ),
    }


# ============================================================
# OFFLOAD TIMELINE
# ============================================================

def plot_offload_timeline(decision_df: pd.DataFrame):
    offloaded_df = decision_df[
        decision_df["offloaded"] == True
    ].copy()

    if offloaded_df.empty:
        print("[Analyzer] No offloaded requests. Skipping timeline.")
        return

    offloaded_df = offloaded_df.sort_values("timestamp")

    # Map node IDs to integer positions for a categorical Y axis.
    selected_nodes = sorted(
        offloaded_df["selected_node_id"]
        .astype(str)
        .unique()
    )

    node_to_y = {
        node_id: index
        for index, node_id in enumerate(selected_nodes)
    }

    y = (
        offloaded_df["selected_node_id"]
        .astype(str)
        .map(node_to_y)
    )

    plt.figure(figsize=(11, 5))

    plt.scatter(
        offloaded_df["timestamp"],
        y,
        s=12
    )

    plt.yticks(
        list(node_to_y.values()),
        list(node_to_y.keys())
    )

    plt.xlabel("Time")
    plt.ylabel("Selected Node")
    plt.title("Offload Decision Timeline")
    plt.grid(True, alpha=0.3)

    save_plot("offload_timeline.png")


# ============================================================
# SUMMARY
# ============================================================

def write_summary(
    decision_df,
    resource_df,
    offload_stats,
    local_stats,
    remote_stats
):
    total_requests = len(decision_df)

    scheduler_counts = (
        decision_df["scheduler_name"]
        .astype(str)
        .value_counts()
    )

    decision_reason_counts = (
        decision_df["decision_reason"]
        .astype(str)
        .value_counts()
    )

    admission_counts = (
        decision_df["admission_status"]
        .astype(str)
        .value_counts()
    )

    lines = []

    lines.append("=== RUNTIME ANALYSIS SUMMARY ===")
    lines.append("")
    lines.append(f"Host node: {HOST_ID}")
    lines.append(f"Total requests: {total_requests}")
    lines.append(
        f"Resource samples: {len(resource_df)}"
    )
    lines.append("")

    lines.append("=== OFFLOAD ===")
    lines.append(
        f"Total offloaded: "
        f"{offload_stats['total_offloaded']}"
    )
    lines.append(
        f"Accepted: "
        f"{offload_stats['offload_accepted']}"
    )
    lines.append(
        f"Rejected: "
        f"{offload_stats['offload_rejected']}"
    )
    lines.append(
        f"Acceptance rate: "
        f"{offload_stats['offload_acceptance_rate']:.2f}%"
    )
    lines.append(
        f"Rejection rate: "
        f"{offload_stats['offload_rejection_rate']:.2f}%"
    )
    lines.append("")

    lines.append("=== LOCAL INFERENCE ===")
    lines.append(
        f"Total local inference: "
        f"{local_stats['total_local_inference']}"
    )
    lines.append("")

    lines.append("=== REMOTE REQUESTS ===")
    lines.append(
        f"Received from other nodes: "
        f"{remote_stats['remote_received']}"
    )
    lines.append(
        f"Remote -> local inference: "
        f"{remote_stats['remote_infer_local']}"
    )
    lines.append(
        f"Remote -> offload again: "
        f"{remote_stats['remote_offloaded_again']}"
    )
    lines.append(
        f"Remote requests with host snapshot: "
        f"{remote_stats['remote_with_host_snapshot']}"
    )
    lines.append("")

    lines.append("=== SCHEDULERS ===")
    for name, count in scheduler_counts.items():
        lines.append(f"{name}: {count}")
    lines.append("")

    lines.append("=== DECISION REASONS ===")
    for reason, count in decision_reason_counts.items():
        lines.append(f"{reason}: {count}")
    lines.append("")

    lines.append("=== ADMISSION STATUS ===")
    for status, count in admission_counts.items():
        lines.append(f"{status}: {count}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    summary_path = OUTPUT_DIR / "summary.txt"

    summary_path.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )

    print(f"[Analyzer] Wrote {summary_path}")


# ============================================================
# MAIN
# ============================================================

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    CSV_DIR.mkdir(parents=True, exist_ok=True)

    decision_df, resource_df = load_logs()

    print(
        f"[Analyzer] Loaded "
        f"{len(decision_df)} decision records"
    )
    print(
        f"[Analyzer] Loaded "
        f"{len(resource_df)} resource records"
    )

    # 1. Resource logger plots
    plot_host_resources(resource_df)

    # 2. Scheduler decision snapshots
    plot_decision_node_resources(decision_df)

    # 3. Offload statistics + CSV
    offload_stats = analyze_offloads(decision_df)

    # 4. Local inference statistics + CSV
    local_stats = analyze_local_inference(decision_df)

    # 5. Remote request analysis
    remote_stats = analyze_remote_requests(decision_df)

    # 6. Offload timeline
    plot_offload_timeline(decision_df)

    # 7. Summary
    write_summary(
        decision_df,
        resource_df,
        offload_stats,
        local_stats,
        remote_stats
    )

    print("\n[Analyzer] Analysis completed.")


if __name__ == "__main__":
    main()
