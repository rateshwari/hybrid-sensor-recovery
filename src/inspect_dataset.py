from pathlib import Path

import pandas as pd

RAW_FILE = Path("data/raw/intel_lab_data.txt")

COLUMNS = [
    "date",
    "time",
    "epoch",
    "node_id",
    "temperature",
    "humidity",
    "light",
    "voltage",
]


def main() -> None:
    if not RAW_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {RAW_FILE}")

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

    sensor_columns = ["temperature", "humidity", "light", "voltage"]

    print("\n=== DATASET OVERVIEW ===")
    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")
    print(f"Unique node IDs: {df['node_id'].nunique()}")
    print(f"Invalid timestamps: {df['timestamp'].isna().sum():,}")

    print("\n=== NODE COUNTS (TOP 10) ===")
    print(df["node_id"].value_counts().head(10).to_string())

    print("\n=== SENSOR VALUE SUMMARY ===")
    print(df[sensor_columns].describe().T.to_string())

    print("\n=== MISSING VALUES ===")
    print(df[sensor_columns].isna().sum().to_string())

    print("\n=== TIMESTAMP RANGE ===")
    print(f"Start: {df['timestamp'].min()}")
    print(f"End:   {df['timestamp'].max()}")

    print("\n=== SAMPLE RECORDS ===")
    print(df.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
