"""Analyze conductance read noise versus voltage for each device and state."""

from pathlib import Path
import re

import matplotlib.pyplot as plt
import pandas as pd


DATA_DIR = Path(__file__).parent / "data" / "removed_outliers_1000"
OUTPUT_DIR = Path(__file__).parent / "figures" / "removed_outliers_1000_read_noise"
VOLTAGE_COLUMN = 3  # Column 4 using one-based numbering.
CONDUCTANCE_COLUMNS = [column - 1 for column in range(15, 61, 5)]


def device_name(csv_path: Path) -> str:
    match = re.search(r"train_samples_(dev_.+?)_1000_samples_", csv_path.name)
    if match is None:
        raise ValueError(f"Could not determine device name from {csv_path.name}")
    return match.group(1)


def summarize_file(csv_path: Path) -> pd.DataFrame:
    data = pd.read_csv(csv_path)
    required_column = max([VOLTAGE_COLUMN, *CONDUCTANCE_COLUMNS])
    if data.shape[1] <= required_column:
        raise ValueError(f"{csv_path.name} does not contain all requested columns")

    states = data.iloc[:, 0].astype(str).str.strip().str.lower()
    voltages = pd.to_numeric(data.iloc[:, VOLTAGE_COLUMN], errors="coerce")
    conductance = data.iloc[:, CONDUCTANCE_COLUMNS].apply(pd.to_numeric, errors="coerce") * 1e6

    row_mean = conductance.mean(axis=1)
    row_read_noise = conductance.std(axis=1, ddof=1)
    summary = pd.DataFrame(
        {
            "state": states,
            "voltage": voltages,
            "mean_conductance_us": row_mean,
            "read_noise_us": row_read_noise,
        }
    ).dropna()

    summary["device"] = device_name(csv_path)
    return summary


def plot_state(summary: pd.DataFrame, state: str, device: str) -> Path:
    state_summary = summary[summary["state"] == state].sort_values("voltage")
    if state_summary.empty:
        raise ValueError(f"No {state} rows found for {device}")

    output_dir = OUTPUT_DIR / state
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{device}_{state}_read_noise_vs_conductance.png"

    figure, axis = plt.subplots(figsize=(9, 6))
    bins = axis.hexbin(
        state_summary["mean_conductance_us"],
        state_summary["read_noise_us"],
        gridsize=25,
        mincnt=1,
        bins="log",
        cmap="YlOrRd",
    )
    figure.colorbar(bins, ax=axis, label="Measurements per bin")
    axis.set_xlabel("Mean conductance (µS)")
    axis.set_ylabel("Read noise: temporal conductance SD (µS)")
    axis.set_title(f"Device {device.removeprefix('dev_')} - {state}: read noise")
    axis.grid(True, alpha=0.25)
    axis.set_ylim(0, 3)
    figure.tight_layout()
    figure.savefig(output_path, dpi=300)
    plt.close(figure)
    return output_path


def main() -> None:
    csv_files = sorted(DATA_DIR.glob("*.csv"))
    if len(csv_files) != 10:
        raise RuntimeError(f"Expected 10 CSV files, found {len(csv_files)}")

    all_summaries = []
    for csv_path in csv_files:
        summary = summarize_file(csv_path)
        all_summaries.append(summary)
        device = device_name(csv_path)
        for state in ("set", "reset"):
            print(f"Saved {plot_state(summary, state, device)}")

    combined_summary = pd.concat(all_summaries, ignore_index=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary_path = OUTPUT_DIR / "read_noise_summary.csv"
    combined_summary.to_csv(summary_path, index=False)
    print(f"Saved {summary_path}")


if __name__ == "__main__":
    main()