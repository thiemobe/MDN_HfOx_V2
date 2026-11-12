"""Plot column 15 conductance values for repeated-measurement CSV files."""

import re
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import rcParams
import pandas as pd

plt.rcParams.update({
    "font.family": "arial",
    "font.size": 14,
    "axes.labelsize": 14,
    "axes.titlesize": 15,
    "xtick.labelsize": 14,
    "ytick.labelsize": 14,
    "legend.fontsize": 14,
})
DATA_DIR = Path(__file__).parent / "data" / "repeated_measurements"
OUTPUT_DIR = Path(__file__).parent / "figures" / "repeated_measurements_conductance"
CONDUCTANCE_COLUMN = 14  # Column 15 using one-based numbering.
RATIO_COLORMAPS = {"high": "YlOrBr", "low": "BuPu"}
LEGACY_FILE_GROUPS = {
    "05_set": "_05_set.csv",
    "08_reset": "_08_reset.csv",
}
VOLTAGE_RATIO_PATTERN = re.compile(
    r"_(?P<voltage>\d+_\d+)_reset_samples_(?P<ratio>high|low)_ratio"
    r"(?:_test)?\.csv$"
)


def file_group(csv_path: Path) -> str:
    match = VOLTAGE_RATIO_PATTERN.search(csv_path.name)
    if match:
        return f"{match.group('voltage')}_reset_{match.group('ratio')}_ratio"

    for group, ending in LEGACY_FILE_GROUPS.items():
        if csv_path.name.endswith(ending):
            return group
    raise ValueError(f"Unrecognized repeated-measurement filename: {csv_path.name}")


def plot_file(csv_path: Path) -> Path:
    data = pd.read_csv(csv_path)

    if data.shape[1] <= CONDUCTANCE_COLUMN:
        raise ValueError(f"{csv_path.name} has fewer than 15 columns")

    states = data.iloc[:, 0].astype(str).str.strip()
    conductance_us = pd.to_numeric(data.iloc[:, CONDUCTANCE_COLUMN]) * 1e6

    suffix = "low_ratio" if "_low_ratio" in csv_path.stem else "high_ratio"
    output_dir = OUTPUT_DIR / suffix
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{csv_path.stem}.png"

    x_values = range(len(data))
    figure, axis = plt.subplots(figsize=(10, 6))
    axis.plot(x_values, conductance_us, color="#176b87", linewidth=1.8, marker="o", markersize=4)
    axis.set_xlabel("State (column 1)")
    axis.set_ylabel("Conductance (µS)")
    axis.set_title(csv_path.stem)
    axis.set_xticks(list(x_values), states.tolist(), rotation=45, ha="right")
    axis.grid(True, alpha=0.25)
    figure.tight_layout()
    figure.savefig(output_path, dpi=300)
    plt.close(figure)

    return output_path


def plot_combined(csv_files: list[Path], group: str) -> Path:
    output_dir = OUTPUT_DIR / "combined"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{group}_combined.png"

    figure, axis = plt.subplots(figsize=(6, 5))
    ratio_key = "high" if "high_ratio" in group else "low" if "low_ratio" in group else None
    purple_shades = plt.colormaps[RATIO_COLORMAPS.get(ratio_key, "YlOrBr")]
    curves = []

    for csv_path in csv_files:
        data = pd.read_csv(csv_path)
        if data.shape[1] <= CONDUCTANCE_COLUMN:
            raise ValueError(f"{csv_path.name} has fewer than 15 columns")

        conductance_us = pd.to_numeric(
            data.iloc[:, CONDUCTANCE_COLUMN], errors="coerce"
        ) * 1e6
        device_tokens = csv_path.stem.split("_")
        device_label = f"{device_tokens[3]}_{device_tokens[4]}"
        curves.append((csv_path, conductance_us, device_label))

    curves.sort(key=lambda curve: curve[1].mean(), reverse=True)
    for index, (_, conductance_us, device_label) in enumerate(curves):
        color_position = 0.9 - 0.55 * index / max(len(curves) - 1, 1)
        axis.plot(
            range(len(conductance_us)),
            conductance_us,
            color=purple_shades(color_position),
            linewidth=1.7,
            label=f"Device {device_label}",
        )

    axis.set_xlabel("Voltage pulse index")
    axis.set_ylabel("Conductance [µS]")
    #axis.set_title(f"Repeated-measurement conductance: {group}")
    axis.grid(True, which="major", alpha=0.25)
    axis.legend()
    COMBINED_X_TICKS = [0, 5, 10, 15]
    COMBINED_Y_TICKS = [20, 50, 80, 110, 140]
    axis.set_xticks(COMBINED_X_TICKS)
    axis.set_yticks(COMBINED_Y_TICKS)
    figure.tight_layout()
    figure.savefig(output_path, dpi=300)
    plt.close(figure)
    return output_path


def plot_mean_by_ratio(csv_files: list[Path], ratio: str | None) -> Path:
    """Mean ± std per voltage; ratio=None pools high- and low-ratio devices."""
    purple_shades = plt.colormaps[RATIO_COLORMAPS.get(ratio, "PuBuGn")]
    ratio_label = ratio if ratio is not None else "high_and_low"
    output_dir = OUTPUT_DIR / "combined" / "mean_std"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{ratio_label}_ratio_mean_std.png"
    voltage_curves: dict[str, list[pd.Series]] = {}

    for csv_path in csv_files:
        match = VOLTAGE_RATIO_PATTERN.search(csv_path.name)
        if not match or (ratio is not None and match.group("ratio") != ratio):
            continue

        data = pd.read_csv(csv_path)
        if data.shape[1] <= CONDUCTANCE_COLUMN:
            raise ValueError(f"{csv_path.name} has fewer than 15 columns")

        conductance_us = pd.to_numeric(
            data.iloc[:, CONDUCTANCE_COLUMN], errors="coerce"
        ) * 1e6
        voltage_curves.setdefault(match.group("voltage"), []).append(conductance_us)

    if not voltage_curves:
        raise ValueError(f"No voltage-specific data found for {ratio_label} ratio")

    figure, axis = plt.subplots(figsize=(6, 5))
    colors = plt.colormaps["tab10"]
    for index, (voltage, curves) in enumerate(sorted(voltage_curves.items())):
        color_position = 0.9 - 0.55 * index / max(len(voltage_curves) - 1, 1)
        measurements = pd.concat(curves, axis=1)
        mean = measurements.mean(axis=1)
        standard_deviation = measurements.std(axis=1)
        x_values = range(len(mean))
        color = colors(index % colors.N)

        axis.plot(
            x_values,
            mean,
            color=purple_shades(color_position),
            linewidth=1.7,
            label=f"{voltage.replace('_', '.')} V (n={len(curves)})",
        )
        if len(curves) > 1:
            axis.fill_between(
                x_values,
                mean - standard_deviation,
                mean + standard_deviation,
                color=purple_shades(color_position),
                alpha=0.2,
                linewidth=0,
            )

    axis.set_xlabel("Voltage pulse index")
    axis.set_ylabel("Conductance [µS]")
    #axis.set_title(f"{ratio.replace('_', ' ').title()} ratio")
    axis.grid(True, which="major", alpha=0.25)
    COMBINED_X_TICKS = [0, 5, 10, 15]
    COMBINED_Y_TICKS = [20, 50, 80, 110, 140]
    axis.set_xticks(COMBINED_X_TICKS)
    axis.set_yticks(COMBINED_Y_TICKS)
    axis.legend(
        title="Applied voltage",
        loc="lower left",
        bbox_to_anchor=(1.02, 0.0),
        borderaxespad=0.0,
    )
    figure.tight_layout()
    
    figure.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(figure)
    return output_path


def main() -> None:
    csv_files = sorted(DATA_DIR.glob("*.csv"))
    selected_files = [
        path for path in csv_files
        if VOLTAGE_RATIO_PATTERN.search(path.name)
        or any(path.name.endswith(ending) for ending in LEGACY_FILE_GROUPS.values())
    ]
    if not selected_files:
        raise RuntimeError(f"No matching CSV files found in {DATA_DIR}")

    grouped_files: dict[str, list[Path]] = {}
    for csv_path in selected_files:
        group = file_group(csv_path)
        grouped_files.setdefault(group, []).append(csv_path)
        output_path = plot_file(csv_path)
        print(f"Saved {output_path}")

    for group, group_files in sorted(grouped_files.items()):
        output_path = plot_combined(group_files, group)
        print(f"Saved {output_path}")

    voltage_files = [
        path for path in selected_files if VOLTAGE_RATIO_PATTERN.search(path.name)
    ]
    for ratio in ("high", "low", None):
        output_path = plot_mean_by_ratio(voltage_files, ratio)
        print(f"Saved {output_path}")


if __name__ == "__main__":
    main()