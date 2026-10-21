# Research Plan

## Primary research question

Under which channel conditions and redundancy budgets does combining
fountain coding with AI-based sensor reconstruction improve recovery
quality compared with unprotected transmission, Reed-Solomon coding,
and fountain coding alone?

## Hypotheses to test

1. Reed-Solomon can correct errors within its correction capability.
2. Interleaving can improve resilience to certain burst-error patterns.
3. Fountain decoding can recover source packets when enough useful
   encoded symbols are received.
4. AI reconstruction may reduce sensor-value error when conventional
   decoding leaves residual gaps and the data contains useful structure.

These are hypotheses, not established findings.

## Experimental controls

- Document the dataset, quantization, packet format, and code parameters.
- Record channel parameters and random seeds.
- Compare communication overhead and recovery performance.
- Repeat experiments across independent trials.
- Prevent train/test leakage in AI reconstruction.
- Report exact packet recovery separately from approximate value recovery.

## Completion criteria

- Tested data representation and packetization.
- Validated channel simulators.
- Tested implementations of the four approaches.
- AI model compared against interpolation.
- Reproducible evaluation scripts, results, and figures.
- Working demonstration and final research deliverables.
