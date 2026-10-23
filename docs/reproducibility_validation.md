# Research Reproducibility Validation

## Overview

This document records reproducibility checks performed on the
burst-resilient IoT sensor recovery experiments.

## Dataset Reproducibility

The raw Intel Lab dataset was processed using:

1. src/prepare_dataset.py
2. src/select_experiment_segment.py

Both processed datasets were regenerated in an isolated temporary
directory and matched their original SHA-256 fingerprints exactly.

Final experiment segment:
- Sensor node: 48
- Variables: temperature and humidity
- Records: 16,326
- Missing values: 0
- SHA-256: 2d76127e56aeb8af12357b9d3c343d7ead8d98775511345fbc54faa7a64038cd

## Automated Testing

Command:

    PYTHONPATH=src python -m pytest tests/ -q

Result:

    28 passed

## Experimental Configuration

- Channel: Gilbert-Elliott burst packet loss
- Target loss rates: 5%, 10%, 25%, 50%, 75%
- Trials per condition: 30
- Random seeds: 42 through 71
- Recovery configurations: 10
- Total published experiment records: 1,500

## Published Results Integrity

Command:

    PYTHONPATH=src python src/final_results_validation.py

Result:

    PASS: All final experimental data checks passed.

Validated structure:
- 1,500 experiment records
- 10 recovery configurations
- 5 loss levels
- 30 trials per condition
- 50 summary records

## Independent Experimental Reproduction

The burst experiment's run_trial() function was rerun without
overwriting published results.

Reproduced conditions:

- Seed 42: all five loss rates, 50 method-level records
- Seed 43: 25% loss, 10 method-level records
- Seed 55: 25% loss, 10 method-level records
- Seed 71: 25% loss, 10 method-level records

Total independently reproduced records: 80

Matching records: 80

Comparison tolerance for numeric values: 1e-9

Execution-time measurements were excluded because runtime
performance varies between executions.

## Limitations

- Only 80 of 1,500 experiment records were independently regenerated.
- The remaining 1,420 records have not been independently rerun.
- Reproduction was performed in the existing local software environment.
- Independent reproduction on another machine has not been verified.
- Execution-time measurements are environment-dependent.
- Dataset checksums verify byte-for-byte identity, not source-data accuracy.

## Conclusion

The dataset preprocessing pipeline reproduced its outputs exactly.

All 1,500 published experimental records passed the project's
integrity checks.

Additionally, all 80 independently regenerated method-level
records matched their corresponding published results for the
compared non-timing fields.

These results support reproducibility under the tested conditions,
but do not establish exhaustive cross-environment reproducibility.
