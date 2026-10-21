# Burst-Error-Resilient Data Recovery for Edge Devices

## Research objective

Evaluate and compare four approaches for recovering sensor data damaged
during transmission:

1. No Error-Correcting Code (No-ECC)
2. Reed-Solomon coding, including an interleaved variant
3. Fountain coding, beginning with LT codes
4. Fountain coding followed by GenAI-based reconstruction

## Channel conditions

- Independent random bit errors
- Burst bit errors using a Gilbert-Elliott channel
- Independent packet loss
- Bursty packet loss

## Research pipeline

Sensor data -> 16-bit quantization -> packetization and CRC
-> coding -> channel damage -> decoding -> optional AI reconstruction
-> evaluation

## Evaluation

- Exact recovery rate
- Residual bit-error rate and packet-error rate
- MAE and RMSE for reconstructed sensor values
- Transmission overhead
- Encoding and decoding time
- Memory usage and model size

## Project structure

- `data/raw/`: locally stored source datasets
- `data/processed/`: cleaned and prepared datasets
- `src/`: implementation modules
- `tests/`: correctness and regression tests
- `configs/`: experiment configurations
- `results/figures/`: generated plots
- `results/tables/`: experiment summaries
- `notebooks/`: exploratory analysis and demonstrations
- `docs/`: research methodology and documentation

## Research principles

- Compare methods using documented and fair experimental conditions.
- Keep exact decoding separate from approximate AI reconstruction.
- Use reproducible random seeds and repeated trials.
- Report measured results honestly, including failures and limitations.
- Do not assume any method is superior before evaluating the evidence.

## Status

Initial repository setup. Implementation and experiments have not yet begun.
