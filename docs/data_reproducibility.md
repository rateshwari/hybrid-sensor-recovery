# Dataset Reproducibility

## Dataset

This project uses the Intel Berkeley Research Lab sensor dataset.

The experiments use readings from sensor node 48, specifically:
- Temperature
- Humidity

The raw dataset is not distributed with this repository.

## Raw Data

Expected local file:

data/raw/intel_lab_data.txt

The raw file must be obtained from the original dataset provider.

SHA-256 of the raw file used in this study:

21d156880db48eb140390beffc18b017282777cdc41e30e665072544ecf0913e

## Preprocessing

Run from the repository root:

    python src/prepare_dataset.py

The script:
1. Selects sensor node 48.
2. Retains temperature and humidity.
3. Removes invalid timestamps.
4. Treats temperatures outside [-40, 85] as missing.
5. Treats humidity outside [0, 100] as missing.
6. Aggregates duplicate timestamps by mean.
7. Resamples readings to one-minute intervals.
8. Interpolates internal gaps of up to five consecutive minutes.

Output:

data/processed/node48_sensor_data.csv

Expected rows: 48,855

Expected SHA-256:

03c9bcbc9b1bc14419dd06d94ded5af3979c4cbd4d452ffe9e53f957750836a7

## Experiment Segment

Run:

    python src/select_experiment_segment.py

The experiment uses the inclusive time interval:

2004-02-28 01:06:00 to 2004-03-10 09:11:00

Output:

data/processed/experiment_segment.csv

Expected records: 16,326

Expected missing temperature values: 0

Expected missing humidity values: 0

Expected SHA-256:

2d76127e56aeb8af12357b9d3c343d7ead8d98775511345fbc54faa7a64038cd

## Verification

Calculate the final dataset fingerprint:

    shasum -a 256 data/processed/experiment_segment.csv

The fingerprint should match the expected SHA-256 above.

Both processed datasets were regenerated in an isolated temporary directory and matched their original SHA-256 fingerprints exactly.

This confirms deterministic preprocessing for the tested raw data, code, and software environment.

## Limitations

- The validity ranges are provisional preprocessing thresholds.
- Short missing intervals are interpolated rather than directly observed.
- The complete resampled node 48 dataset contains missing values outside the selected experiment interval.
- Reproducibility across different software environments has not yet been independently verified.
