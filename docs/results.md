# 5. Results and Discussion

## 5.1 Experimental Overview

The experiments evaluated error-recovery performance using three implemented approaches: No Error Correction (No ECC), Reed–Solomon coding with an 8+2 configuration, and Fountain coding at 1.5× and 2.0× transmission factors. Two packet-loss scenarios were considered: independent random packet loss and burst packet loss simulated using a Gilbert–Elliott channel model.

The random-loss experiment evaluated configured packet-loss rates of 5%, 10%, 20%, and 30%, with 30 trials per method and loss rate. The burst-loss experiment evaluated recovery over 30 trials per method. Performance was measured using exact source-packet recovery, complete source recovery, transmission count, and software encoding and decoding time.

The reported results represent software simulations on the development environment. They should not be interpreted as measurements from a physical edge device.

## 5.2 Results Under Independent Random Packet Loss

The random-loss experiments demonstrated that the redundancy level substantially influenced packet recovery. No ECC exhibited progressively lower mean exact packet recovery as the configured loss rate increased, declining from 94.87% at 5% loss to 69.48% at 30% loss.

Reed–Solomon (8+2) improved mean exact recovery to 99.70%, 97.98%, 88.78%, and 75.51% at the respective loss rates of 5%, 10%, 20%, and 30%. Its transmission count was 320 packets for 256 source packets, corresponding to 25% packet-count overhead.

Fountain coding at 1.5× achieved 99.90%, 99.88%, and 97.85% mean exact recovery at loss rates of 5%, 10%, and 20%, respectively. At 30% loss, its recovery declined to 70.78%, falling below the Reed–Solomon result. This indicates that the lower Fountain redundancy configuration did not consistently outperform Reed–Solomon under the highest tested loss rate.

Fountain coding at 2.0× achieved 100.00% mean exact recovery at 5% and 10% loss, 99.99% at 20% loss, and 99.34% at 30% loss. It also achieved complete source recovery in 66.67% of trials at 30% loss, compared with no complete-recovery trials for No ECC or Reed–Solomon at that rate.

These findings suggest that increased Fountain redundancy can improve recovery under the tested random-loss conditions. However, the improvement comes at a higher transmission cost: 512 transmitted symbols for 256 source packets, or 100% symbol-count overhead in the current implementation.

## 5.3 Results Under Burst Packet Loss

The burst-loss experiment used a Gilbert–Elliott channel model to represent correlated packet erasures. Mean exact source-packet recovery was 90.99% for No ECC, 93.35% for Reed–Solomon (8+2), 97.20% for Fountain (1.5×), and 99.96% for Fountain (2.0×).

Fountain (2.0×) achieved complete source recovery in 28 of 30 trials (93.33%). Fountain (1.5×) achieved complete source recovery in 10 of 30 trials (33.33%). Neither No ECC nor Reed–Solomon achieved complete source recovery in any of the 30 trials, despite their nonzero mean packet-recovery rates.

The 95% confidence intervals for mean exact source-packet recovery were 89.61–92.37% for No ECC, 92.07–94.63% for Reed–Solomon, 95.62–98.78% for Fountain (1.5×), and 99.90–100.00% for Fountain (2.0×). The interval for Fountain (2.0×) is bounded at 100% because recovery cannot exceed that value.

The burst-loss results indicate that the higher-redundancy Fountain configuration performed best among the tested methods under the simulated channel. The difference between Fountain (1.5×) and Fountain (2.0×) also highlights the relationship between redundancy and the probability of recovering the complete source.

## 5.4 Statistical Comparison

Pairwise statistical tests were conducted on mean packet-recovery rates, followed by Holm–Bonferroni adjustment to account for six comparisons. All six comparisons remained statistically significant at the 0.05 level under the selected testing procedures.

For Reed–Solomon versus No ECC, a paired t-test was appropriate because both methods shared matched source-loss patterns across the same 30 trial seeds. Reed–Solomon improved mean recovery by 2.36 percentage points, with a 95% confidence interval of 1.97–2.74 percentage points and a paired-test p-value of approximately 2.66 × 10⁻¹³.

Fountain (1.5×) exceeded No ECC by 6.21 percentage points and Reed–Solomon by 3.85 percentage points in the burst-loss experiment. Fountain (2.0×) exceeded No ECC by 8.97 percentage points and Reed–Solomon by 6.61 percentage points. The comparison between the two Fountain configurations showed a 2.76-percentage-point improvement for Fountain (2.0×).

The Fountain-versus-baseline comparisons used Welch’s independent-samples t-test because the methods used different channel-seed realizations. The Fountain-overhead comparison used a paired test based on shared trial seeds; because the encoded streams differ in length, this pairing should be interpreted with care. The p-values provide evidence of differences under the current simulation design, not proof of universal superiority across all channel conditions.

## 5.5 Transmission Overhead and Computational Cost

No ECC transmitted 256 packets for 256 source packets. Reed–Solomon (8+2) transmitted 320 packets, while Fountain (1.5×) and Fountain (2.0×) transmitted 384 and 512 symbols, respectively. These correspond to nominal symbol-count overheads of 0%, 25%, 50%, and 100%.

The results therefore reveal a trade-off between transmission cost and recovery performance. Fountain (2.0×) achieved the highest recovery, but required twice as many transmitted symbols as source packets. Reed–Solomon used less redundancy than either Fountain configuration, but recovered fewer source packets in the tested burst-loss scenario.

Encoding and decoding times were measured using software timers. These measurements characterize the current implementation on the development environment; they do not establish the energy consumption, latency, or computational performance of deployment on an actual edge device. Furthermore, the current symbol-count accounting does not include all byte-level framing and metadata costs.

## 5.6 Limitations

Several limitations must be considered when interpreting these findings.

First, the experiments use one sensor-data segment and a limited set of channel configurations. Results may differ with other datasets, packet sizes, loss rates, or burst-transition probabilities.

Second, the burst experiment evaluates packet erasures using a Gilbert–Elliott model. It does not establish performance under burst bit corruption. Separate bit-error experiments would be required for that claim.

Third, the Reed–Solomon transmission model appends parity packets after source packets. An interleaved transmission design may behave differently under burst loss.

Fourth, the current Fountain implementation is a research prototype and should not be treated as equivalent to a production RaptorQ implementation. Its reported overhead is based on transmitted symbol counts rather than complete network bytes.

Finally, the Generative AI reconstruction method has not yet been included in the reported comparisons. The present results therefore compare No ECC, Reed–Solomon, and two Fountain redundancy configurations, rather than a completed four-method evaluation.

## 5.7 Summary

Across the tested conditions, Fountain (2.0×) achieved the highest observed exact source-packet recovery under both independent random packet loss and simulated burst packet loss. Fountain (1.5×) offered a lower-redundancy alternative but did not outperform Reed–Solomon at the highest tested random-loss rate. Reed–Solomon improved burst-loss recovery relative to No ECC while using less nominal redundancy than either Fountain configuration.

Overall, the experiments demonstrate a measurable trade-off between recovery performance and transmission overhead within the implemented simulation framework. Further evaluation across additional datasets and channel settings, together with implementation of the Generative AI reconstruction baseline, is needed before drawing broader conclusions about hybrid recovery methods for edge devices.