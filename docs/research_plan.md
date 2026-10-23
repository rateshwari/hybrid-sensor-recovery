# Research Plan

## Research Scope

This study evaluates packet-erasure recovery for IoT sensor data
using Reed-Solomon coding, packet interleaving, and Fountain coding.

The original proposal included AI-based sensor reconstruction.
That component was excluded from the finalized experimental scope.

The final study evaluates exact packet recovery rather than
approximate reconstruction of missing sensor values.

## Primary Research Question

How do Reed-Solomon coding, packet interleaving, and Fountain
coding compare in exact sensor packet recovery under independent
and burst packet-loss conditions?

How do recovery performance, redundancy overhead, execution
time, and memory requirements vary across channel conditions?

## Research Hypotheses

1. Reed-Solomon coding can recover erased source packets when
   the number of erasures within a code block does not exceed
   the available parity capacity.

2. Interleaving can improve Reed-Solomon recovery under
   certain burst-loss conditions by redistributing consecutive
   packet erasures across code blocks.

3. Fountain coding can recover source packets when sufficient
   linearly independent encoded symbols are received.

4. Recovery performance depends on channel conditions,
   redundancy budget, and coding configuration.

5. Higher redundancy can improve recovery performance but
   increases transmission overhead and may increase
   computational resource requirements.

## Experimental Design

Dataset:
- Intel Berkeley Research Lab sensor dataset
- Sensor node 48
- Temperature and humidity
- 16,326 experiment records

Packetization:
- Packet size: 256 bytes

Channel models:
- Independent random packet loss
- Gilbert-Elliott burst packet loss

Target packet-loss rates:
- 5%
- 10%
- 25%
- 50%
- 75%

Recovery configurations:
- No ECC
- Reed-Solomon (8+2)
- Reed-Solomon (8+4)
- Reed-Solomon (8+8)
- RS Interleaved (8+2)
- RS Interleaved (8+4)
- RS Interleaved (8+8)
- Fountain (1.25x)
- Fountain (1.50x)
- Fountain (2.00x)

Repeated evaluation:
- 30 trials per condition
- Random seeds 42 through 71

## Evaluation Metrics

- Packet recovery percentage
- Transmission redundancy
- Encoding execution time
- Decoding execution time
- Peak Python memory allocation
- Statistical confidence intervals
- Paired interleaving recovery gain

## Experimental Controls

- Document dataset preparation and packetization.
- Record channel parameters and random seeds.
- Use controlled packet-loss conditions.
- Compare recovery performance across configurations.
- Repeat experiments across independent trials.
- Report exact packet recovery.
- Evaluate communication and computational tradeoffs.
- Preserve reproducible scripts, results, and figures.

## Completion Criteria

- Validated sensor data representation and packetization.
- Tested independent and burst-loss channel simulators.
- Tested Reed-Solomon and Fountain implementations.
- Evaluated interleaving under burst loss.
- Completed repeated recovery experiments.
- Compared redundancy and computational costs.
- Performed statistical analysis.
- Validated published experimental results.
- Documented reproducibility and limitations.
- Prepared final research deliverables.

## Scope Limitations

- AI-based sensor-value reconstruction is excluded.
- Recovery is evaluated at the packet-erasure level.
- Computational timing is not equivalent to network latency.
- Peak Python allocation is not total process memory.
- Cross-machine experimental reproducibility remains unverified.
