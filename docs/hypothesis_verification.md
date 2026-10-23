# Research Hypothesis Verification

## Project
Burst-Error-Resilient Sensor Data Recovery Using Reed-Solomon, Interleaving, and Fountain Codes

## Experimental Setup
- Dataset: Intel Berkeley Lab sensor readings, node 48
- Source packets: 256
- Packet size: 256 bytes
- Channel models: IID packet erasure and Gilbert-Elliott burst erasure
- Target packet-loss rates: 5%, 10%, 25%, 50%, 75%
- Random seeds: 42 through 71
- Trials per configuration: 30
- Recovery metric: exact source-packet recovery

## H1: Reed-Solomon Erasure Recovery

**Status: Supported in controlled tests.**

Reed-Solomon coding recovered erased packets when the number
of erasures remained within the configured parity capacity.

For RS(8+4):
- Two erasures: 8/8 source packets recovered
- Four erasures: 8/8 source packets recovered
- Five erasures: recovery capacity exceeded

## H2: Interleaving Under Burst Loss

**Status: Supported conditionally.**

Interleaving redistributed consecutive packet erasures
across Reed-Solomon groups.

At 25% target burst loss:
- RS(8+2): +4.167 percentage points
- RS(8+4): +8.724 percentage points
- RS(8+8): +5.521 percentage points

However, interleaving did not improve recovery under every
tested condition. Negative effects were observed for some
configurations at 50% target loss.

## H3: Fountain Decoding

**Status: Supported in controlled tests.**

The Fountain decoder recovered source packets from sufficient
linearly independent encoded equations.

Controlled tests confirmed:
- Three independent equations: complete recovery
- Three dependent equations: no uniquely determined packets
  in the tested system
- Partial recovery when a singleton equation was available
- Exact recovery of all 32 source packets in a no-loss
  end-to-end encoding/decoding test

## H4: Channel-Dependent Recovery

**Status: Supported by experimental comparisons.**

IID and burst-erasure experiments used the same five target
loss levels, 30 seeds, and 256 source packets.

At 25% target loss:
- RS(8+4): burst minus IID = -7.81 percentage points
- Fountain (1.50x): -16.99 percentage points
- Fountain (1.25x): +8.95 percentage points

Six of seven unadjusted 95% bootstrap confidence intervals
excluded zero. No multiple-comparison adjustment was applied.

Differences should not be attributed solely to burstiness
without controlling for realized packet-loss rates.

## H5: Redundancy-Recovery Tradeoff

**Status: Supported within tested configurations.**

For Fountain coding, mean recovery increased monotonically
with redundancy across all five target burst-loss levels.

At 25% target burst loss:
- Fountain 1.25x: 47.62% recovery
- Fountain 1.50x: 71.78% recovery
- Fountain 2.00x: 96.46% recovery

At 75% target loss, Fountain 2.00x recovered only 6.16%
of source packets on average.

Higher redundancy increases transmitted symbol count and
communication overhead. Resource costs are reported
separately in the performance results.

## Statistical Method

- Bootstrap confidence intervals: percentile method
- IID-versus-burst bootstrap samples: 10,000
- IID and burst trials resampled independently
- Confidence level: 95%
- Interleaving comparisons used paired bootstrap analysis
- Confidence intervals are unadjusted for multiple comparisons

## Limitations

1. Results are based on one selected sensor-data segment.
2. Burst-channel results depend on the chosen transition parameters.
3. Realized packet loss can differ from the target loss rate.
4. Timing measurements reflect implementation execution time,
   not end-to-end network latency.
5. Tracemalloc measurements capture tracked Python allocations,
   not complete process memory usage.
6. Findings are specific to the tested packet sizes, block sizes,
   redundancy configurations, and decoder implementations.
7. No AI-based reconstruction is included in the final study.

## Supporting Results

- results/tables/final_performance_comparison.csv
- results/tables/recovery_confidence_intervals.csv
- results/tables/paired_interleaving_results.csv
- results/tables/iid_vs_burst_bootstrap.csv
- docs/reproducibility_validation.md
- docs/data_reproducibility.md
