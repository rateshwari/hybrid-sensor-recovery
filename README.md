# Burst-Error-Resilient Sensor Data Recovery Using Reed–Solomon, Interleaving, and Fountain Codes

## Project Overview

This research project evaluates packet-level error correction techniques for improving the reliability of IoT sensor data transmitted over unreliable communication channels.

The study compares four approaches:

1. No Error-Correcting Code (No ECC)
2. Reed–Solomon (RS) coding
3. Reed–Solomon coding with packet interleaving
4. LT-style Fountain coding

The objective is to evaluate recovery effectiveness, redundancy requirements, execution time, and memory consumption under independent and bursty packet-loss conditions.

**Scope:** The finalized experiments focus on packet-level error correction. AI-based reconstruction is not included in the reported comparisons.

## Dataset

The experiments use temperature and humidity measurements from Intel Lab sensor node 48.

The prepared dataset contains:

- 16,326 minute-resampled records
- Temperature and humidity measurements
- 256-byte source packets
- 256 source packets per experiment

The processed experimental dataset is read from:

`data/processed/experiment_segment.csv`

The dataset must be prepared before reproducing the experiments.

## Error-Correction Methods

### No ECC

Packets are transmitted without redundancy. Lost packets remain unrecovered.

### Reed–Solomon Coding

The implementation applies Reed–Solomon erasure coding across packet groups, using eight source packets per group.

The evaluated configurations are:

- RS(8+2): 25% redundancy
- RS(8+4): 50% redundancy
- RS(8+8): 100% redundancy

### Reed–Solomon With Interleaving

Encoded packets are interleaved column-wise across RS groups before transmission.

Interleaving distributes consecutive packet losses across multiple codewords, potentially improving recovery under burst-loss conditions without increasing the parity count.

### Fountain Coding

An LT-style Fountain encoder generates XOR combinations of source packets using a Robust Soliton degree distribution.

The decoder uses Gaussian elimination over GF(2) to reconstruct source packets from received encoded symbols.

The evaluated transmission overheads are:

- 1.25×: 25% redundancy
- 1.50×: 50% redundancy
- 2.00×: 100% redundancy

## Channel Models

Two packet-loss models are evaluated:

**Independent packet loss (IID):** Packet erasures occur independently according to the configured loss probability.

**Gilbert–Elliott burst packet loss:** A two-state channel models correlated losses and consecutive packet erasures.

The burst-channel configuration uses a BAD-to-GOOD transition probability of 0.25.

## Experimental Design

The burst-loss evaluation uses:

- Target loss rates: 5%, 10%, 25%, 50%, 75%
- Repeated trials: 30 per loss rate
- Random seeds: 42–71
- Recovery configurations: 10
- Total burst-loss experiment records: 1,500

Experiments measure packet recovery, transmission overhead, encoding and decoding time, and Python memory allocations.

The reported memory measurements use `tracemalloc` peak allocations, not total process memory or resident set size.

Execution timings represent measured software execution time, not network transmission latency.

## Research Findings

The experiments demonstrate that recovery effectiveness depends on channel conditions, redundancy, and coding strategy.

Under the evaluated Gilbert–Elliott burst-loss conditions:

- Interleaved RS(8+8) achieved approximately 99.64% mean source-packet recovery at 25% target loss.
- Fountain coding with 2.00× transmission achieved approximately 96.46% mean recovery at 25% target loss.
- Interleaved RS(8+4) improved mean recovery over standard RS(8+4) by approximately 8.72 percentage points at 25% target loss.
- At 75% target loss, even the highest-redundancy configurations experienced substantial unrecovered data.

These results are specific to the evaluated dataset, channel model, packet sizes, coding configurations, and random trials. They do not establish universal superiority of one coding method.

## Statistical Evaluation

The analysis includes:

- Mean recovery rates across repeated trials
- Bootstrap confidence intervals
- Paired comparisons of standard and interleaved RS configurations
- Recovery-versus-redundancy comparisons
- Encoding and decoding timing comparisons
- Peak Python memory-allocation comparisons

The confidence intervals describe uncertainty under the evaluated simulation setup.

## Installation

The project was developed and tested using Python 3.11.15.

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Running Tests

Run the complete automated test suite:

```bash
PYTHONPATH=src python -m pytest tests/ -v
```

The latest verified run completed successfully with **28 passing tests**.

The tests cover packetization, CRC checks, channel simulation, Reed–Solomon recovery, Fountain decoding, interleaving, and controlled end-to-end byte-for-byte reconstruction.

## Running the Burst-Loss Experiment

From the project root, after preparing the required dataset:

```bash
PYTHONPATH=src python src/burst_experiment.py
```

The experiment writes its detailed results to:

`results/tables/burst_recovery_results.csv`

Additional scripts generate statistical summaries, resource measurements, and research figures.

## Research Outputs

The project stores generated outputs in:

- `results/tables/`: Experimental results and statistical summaries
- `results/figures/`: Recovery, redundancy, timing, memory, and confidence-interval plots
- `tests/`: Unit and integration tests
- `src/`: Recovery algorithms, simulations, and evaluation scripts

## Limitations

- Results are based on a specific sensor dataset and simulated communication channels.
- Fountain decoding success depends on the rank and structure of received encoded symbols.
- Interleaving can improve burst-loss resilience but does not increase RS correction capacity.
- Timing measurements do not include real network latency.
- Memory measurements represent Python allocation peaks rather than complete process memory.
- Reported results do not establish performance on physical IoT hardware.
- The separate Conditional VAE module is experimental and is not included in the finalized packet-recovery comparison.

## Project Status

The packet-level recovery algorithms, channel simulations, repeated experiments, statistical analyses, and automated correctness tests have been implemented.

The current phase focuses on research reproducibility, documentation, and final validation.

## Dataset Reproducibility

The raw Intel Lab sensor dataset is not included in this repository.

For instructions on obtaining the raw data, preprocessing sensor node 48,
recreating the 16,326-record experiment segment, and verifying SHA-256
checksums, see the [Dataset Reproducibility Guide](docs/data_reproducibility.md).
