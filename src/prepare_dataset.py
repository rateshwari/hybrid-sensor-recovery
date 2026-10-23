from pathlib import Path

import pandas as pd

RAW_FILE = Path("data/raw/intel_lab_data.txt")
OUTPUT_FILE = Path("data/processed/node48_sensor_data.csv")
REPORT_FILE = Path("results/tables/node48_data_quality.txt")

COLUMNS = [
    "date", "time", "epoch", "node_id",
    "temperature", "humidity", "light", "voltage",
]

def main():
    df = pd.read_csv(
        RAW_FILE,
        sep=r"\s+",
        header=None,
        names=COLUMNS,
        na_values=["NaN", "nan", "NA"],
        low_memory=False,
    )

    df["timestamp"] = pd.to_datetime(
        df["date"] + " " + df["time"],
        errors="coerce",
    )

    # Select node 48 and the two initial sensor variables.
    node = df.loc[
        df["node_id"].eq(48),
        ["timestamp", "temperature", "humidity"],
    ].copy()

    # Exclude invalid timestamps and physically implausible readings.
    node = node.dropna(subset=["timestamp"])
    node.loc[
        ~node["temperature"].between(-40, 85), "temperature"
    ] = float("nan")
    node.loc[
        ~node["humidity"].between(0, 100), "humidity"
    ] = float("nan")

    # Sort chronologically and aggregate duplicate timestamps.
    node = (
        node.groupby("timestamp")[["temperature", "humidity"]]
        .mean()
        .sort_index()
    )

    # Resample to a one-minute grid.
    regular = node.resample("1min").mean()

    # Interpolate short internal gaps only; do not extrapolate at endpoints.
    regular[["temperature", "humidity"]] = (
        regular[["temperature", "humidity"]]
        .interpolate(method="time", limit=5, limit_area="inside")
    )

    regular.index.name = "timestamp"
    regular = regular.reset_index()

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

    regular.to_csv(OUTPUT_FILE, index=False)

    report = [
        "Dataset preparation report",
        "Source: Intel Lab sensor data",
        "Selected node: 48",
        "Variables: temperature, humidity",
        "Resampling interval: 1 minute",
        "Provisional validity ranges: temperature [-40, 85], humidity [0, 100]",
        "Interpolation: time-based, up to 5 consecutive missing minutes, internal gaps only",
        f"Rows after resampling: {len(regular)}",
        f"Start: {regular['timestamp'].min()}",
        f"End: {regular['timestamp'].max()}",
        "Missing values after interpolation:",
        regular[["temperature", "humidity"]].isna().sum().to_string(),
    ]

    REPORT_FILE.write_text("\n".join(map(str, report)) + "\n")

    print("\n".join(map(str, report)))
    print(f"\nSaved dataset: {OUTPUT_FILE}")
    print(f"Saved report: {REPORT_FILE}")

if __name__ == "__main__":
    main()
