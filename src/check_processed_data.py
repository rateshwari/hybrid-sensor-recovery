import pandas as pd

path = "data/processed/node48_sensor_data.csv"
df = pd.read_csv(path, parse_dates=["timestamp"])

cols = ["temperature", "humidity"]

print("=== OVERALL COMPLETENESS ===")
print((df[cols].notna().mean() * 100).round(2).astype(str).add("%"))

print("\n=== ROWS WITH BOTH VALUES ===")
both = df[cols].notna().all(axis=1)
print(f"{both.sum():,} / {len(df):,} ({both.mean() * 100:.2f}%)")

# Find contiguous one-minute runs where both measurements are present.
group = (~both).cumsum()
runs = (
    df.loc[both]
    .assign(run=group[both].to_numpy())
    .groupby("run")
    .agg(
        rows=("timestamp", "size"),
        start=("timestamp", "min"),
        end=("timestamp", "max"),
    )
    .sort_values("rows", ascending=False)
)

print("\n=== TOP 10 CONTIGUOUS COMPLETE RUNS ===")
print(runs.head(10).to_string())
