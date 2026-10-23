from pathlib import Path

import pandas as pd

SOURCE = Path("data/processed/node48_sensor_data.csv")
OUTPUT = Path("data/processed/experiment_segment.csv")

START = "2004-02-28 01:06:00"
END = "2004-03-10 09:11:00"

def main():
    df = pd.read_csv(SOURCE, parse_dates=["timestamp"])

    segment = df.loc[
        df["timestamp"].between(START, END),
        ["timestamp", "temperature", "humidity"],
    ].copy()

    if segment.empty:
        raise ValueError("Selected experiment segment is empty.")

    if segment[["temperature", "humidity"]].isna().any().any():
        raise ValueError(
            "Selected segment contains missing values; inspect the "
            "data-quality report before continuing."
        )

    expected_rows = int(
        (pd.Timestamp(END) - pd.Timestamp(START)).total_seconds() / 60
    ) + 1

    if len(segment) != expected_rows:
        raise ValueError(
            f"Expected {expected_rows} rows, found {len(segment)}."
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    segment.to_csv(OUTPUT, index=False)

    print("Experiment segment verified")
    print(f"Rows: {len(segment):,}")
    print(f"Start: {segment['timestamp'].min()}")
    print(f"End: {segment['timestamp'].max()}")
    print("Missing values:")
    print(segment[["temperature", "humidity"]].isna().sum().to_string())
    print(f"Saved: {OUTPUT}")

if __name__ == "__main__":
    main()
