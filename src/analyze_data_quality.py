from pathlib import Path

import pandas as pd

RAW_FILE = Path("data/raw/intel_lab_data.txt")

COLUMNS = [
    "date", "time", "epoch", "node_id",
    "temperature", "humidity", "light", "voltage",
]

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

print("\n=== EXTREME TEMPERATURE VALUES ===")
print(
    df.loc[
        df["temperature"].notna()
        & ~df["temperature"].between(-40, 85),
        ["timestamp", "node_id", "temperature"],
    ].head(10).to_string(index=False)
)

print("\n=== EXTREME HUMIDITY VALUES ===")
print(
    df.loc[
        df["humidity"].notna()
        & ~df["humidity"].between(0, 100),
        ["timestamp", "node_id", "humidity"],
    ].head(10).to_string(index=False)
)

valid = df.dropna(
    subset=["timestamp", "node_id", "temperature", "humidity"]
).copy()

# Provisional physical plausibility filters for candidate selection only.
# These are not yet the final research cleaning rules.
valid = valid[
    valid["temperature"].between(-40, 85)
    & valid["humidity"].between(0, 100)
]

summary = valid.groupby("node_id").agg(
    observations=("timestamp", "size"),
    distinct_timestamps=("timestamp", "nunique"),
    first_timestamp=("timestamp", "min"),
    last_timestamp=("timestamp", "max"),
)

summary = summary.sort_values("observations", ascending=False)

print("\n=== TOP 10 CANDIDATE NODES ===")
print(summary.head(10).to_string())

print("\n=== SAMPLING INTERVALS FOR TOP CANDIDATE ===")
if not summary.empty:
    node_id = summary.index[0]
    node = valid[valid["node_id"] == node_id].sort_values("timestamp")
    intervals = node["timestamp"].diff().dt.total_seconds().dropna()

    print(f"Candidate node: {node_id}")
    print(intervals.describe(percentiles=[0.25, 0.5, 0.75, 0.9]).to_string())
