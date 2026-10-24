"use client";

import { apiUrl } from "@/lib/api";
import { useEffect, useState } from "react";

type GainResult = {
  parity: number;
  target_loss_rate: number;
  trials: number;
  mean_gain_pp: number;
  ci_lower_pp: number;
  ci_upper_pp: number;
};

type GainResponse = {
  channel: string;
  comparison: string;
  confidence_level: number;
  parity_values: number[];
  loss_rates: number[];
  results: GainResult[];
};

const WIDTH = 900;
const HEIGHT = 370;
const LEFT = 65;
const RIGHT = 25;
const TOP = 25;
const BOTTOM = 55;

const COLORS: Record<number, string> = {
  2: "#22d3ee",
  4: "#a78bfa",
  8: "#34d399",
};

export default function InterleavingGain() {
  const [data, setData] = useState<GainResponse | null>(null);
  const [selectedParity, setSelectedParity] = useState<number[]>([2, 4, 8]);
  const [selectedLoss, setSelectedLoss] = useState(0.25);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      try {
        const response = await fetch(
          apiUrl("/api/interleaving-gain"),
          { signal: controller.signal }
        );

        if (!response.ok) {
          throw new Error(`API returned ${response.status}`);
        }

        const result: GainResponse = await response.json();

        if (!controller.signal.aborted) {
          setData(result);
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(
            err instanceof Error ? err.message : "Unable to load gain results"
          );
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    load();
    return () => controller.abort();
  }, []);

  const plotWidth = WIDTH - LEFT - RIGHT;
  const plotHeight = HEIGHT - TOP - BOTTOM;

  // All measured confidence intervals fit inside these bounds.
  const MIN_GAIN = -5;
  const MAX_GAIN = 15;

  const x = (loss: number) =>
    LEFT + ((loss - 0.05) / 0.7) * plotWidth;

  const y = (gain: number) =>
    TOP + ((MAX_GAIN - gain) / (MAX_GAIN - MIN_GAIN)) * plotHeight;

  const toggleParity = (parity: number) => {
    setSelectedParity((previous) =>
      previous.includes(parity)
        ? previous.filter((value) => value !== parity)
        : [...previous, parity]
    );
  };

  const selectedRows = (data?.results ?? [])
    .filter(
      (row) =>
        Math.abs(row.target_loss_rate - selectedLoss) < 1e-9 &&
        selectedParity.includes(row.parity)
    )
    .sort((a, b) => a.parity - b.parity);

  return (
    <section className="mt-10 rounded-2xl border border-slate-700 bg-slate-800/60 p-6">
      <h2 className="text-2xl font-bold text-cyan-400">
        Paired Interleaving Gain Analysis
      </h2>

      <p className="mt-2 text-sm text-slate-400">
        Mean recovery difference between interleaved and standard
        Reed–Solomon coding under Gilbert–Elliott burst loss.
        Positive values favor interleaving; negative values favor
        standard RS.
      </p>

      {loading && (
        <p className="mt-5 text-cyan-300">Loading paired results...</p>
      )}

      {error && <p className="mt-5 text-red-400">{error}</p>}

      {data && (
        <>
          <div className="mt-6 flex flex-wrap gap-4">
            {data.parity_values.map((parity) => (
              <label
                key={parity}
                className="flex cursor-pointer items-center gap-2 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200"
              >
                <input
                  type="checkbox"
                  checked={selectedParity.includes(parity)}
                  onChange={() => toggleParity(parity)}
                  style={{ accentColor: COLORS[parity] }}
                />
                RS (8+{parity})
              </label>
            ))}
          </div>

          <div className="mt-6 overflow-x-auto rounded-xl bg-slate-950 p-3">
            <svg
              viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
              className="min-w-[650px] w-full"
              role="img"
              aria-label="Paired interleaving recovery gains with bootstrap confidence intervals"
            >
              {[-5, 0, 5, 10, 15].map((tick) => (
                <g key={tick}>
                  <line
                    x1={LEFT}
                    y1={y(tick)}
                    x2={WIDTH - RIGHT}
                    y2={y(tick)}
                    stroke={tick === 0 ? "#f8fafc" : "#334155"}
                    strokeWidth={tick === 0 ? 2 : 1}
                    strokeDasharray={tick === 0 ? undefined : "4 4"}
                    opacity={tick === 0 ? 0.85 : 1}
                  />
                  <text
                    x={LEFT - 10}
                    y={y(tick) + 4}
                    fill="#94a3b8"
                    fontSize="12"
                    textAnchor="end"
                  >
                    {tick > 0 ? "+" : ""}
                    {tick} pp
                  </text>
                </g>
              ))}

              {data.loss_rates.map((loss) => (
                <text
                  key={loss}
                  x={x(loss)}
                  y={HEIGHT - 30}
                  fill="#94a3b8"
                  fontSize="12"
                  textAnchor="middle"
                >
                  {(loss * 100).toFixed(0)}%
                </text>
              ))}

              {data.parity_values
                .filter((parity) => selectedParity.includes(parity))
                .map((parity) => {
                  const rows = data.results
                    .filter((row) => row.parity === parity)
                    .sort(
                      (a, b) => a.target_loss_rate - b.target_loss_rate
                    );

                  const color = COLORS[parity];

                  const path = rows
                    .map(
                      (row, index) =>
                        `${index === 0 ? "M" : "L"} ${x(
                          row.target_loss_rate
                        )} ${y(row.mean_gain_pp)}`
                    )
                    .join(" ");

                  return (
                    <g key={parity}>
                      <path
                        d={path}
                        fill="none"
                        stroke={color}
                        strokeWidth="2.5"
                      />

                      {rows.map((row) => {
                        const xx = x(row.target_loss_rate);
                        const lower = y(row.ci_lower_pp);
                        const upper = y(row.ci_upper_pp);

                        return (
                          <g key={row.target_loss_rate}>
                            <line
                              x1={xx}
                              y1={upper}
                              x2={xx}
                              y2={lower}
                              stroke={color}
                              strokeWidth="2"
                            />
                            <line
                              x1={xx - 5}
                              y1={upper}
                              x2={xx + 5}
                              y2={upper}
                              stroke={color}
                              strokeWidth="2"
                            />
                            <line
                              x1={xx - 5}
                              y1={lower}
                              x2={xx + 5}
                              y2={lower}
                              stroke={color}
                              strokeWidth="2"
                            />
                            <circle
                              cx={xx}
                              cy={y(row.mean_gain_pp)}
                              r="5"
                              fill={color}
                            >
                              <title>
                                RS (8+{parity}),{" "}
                                {(row.target_loss_rate * 100).toFixed(0)}%
                                loss: {row.mean_gain_pp.toFixed(2)} pp,
                                95% CI [{row.ci_lower_pp.toFixed(2)},{" "}
                                {row.ci_upper_pp.toFixed(2)}] pp
                              </title>
                            </circle>
                          </g>
                        );
                      })}
                    </g>
                  );
                })}

              <text
                x={WIDTH / 2}
                y={HEIGHT - 6}
                fill="#94a3b8"
                fontSize="13"
                textAnchor="middle"
              >
                Target burst packet loss rate
              </text>
            </svg>
          </div>

          <div className="mt-7 flex flex-wrap items-center gap-4">
            <h3 className="text-lg font-semibold text-white">
              Paired Comparison
            </h3>

            <select
              value={selectedLoss}
              onChange={(e) => setSelectedLoss(Number(e.target.value))}
              className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white"
            >
              {data.loss_rates.map((loss) => (
                <option key={loss} value={loss}>
                  {(loss * 100).toFixed(0)}% target loss
                </option>
              ))}
            </select>
          </div>

          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-700 text-slate-400">
                <tr>
                  <th className="py-3">Configuration</th>
                  <th className="py-3">Mean gain</th>
                  <th className="py-3">95% Paired CI</th>
                  <th className="py-3">Trials</th>
                </tr>
              </thead>
              <tbody>
                {selectedRows.map((row) => (
                  <tr
                    key={row.parity}
                    className="border-b border-slate-800 text-slate-200"
                  >
                    <td className="py-3">RS (8+{row.parity})</td>
                    <td
                      className={`py-3 font-semibold ${
                        row.mean_gain_pp >= 0
                          ? "text-emerald-400"
                          : "text-red-400"
                      }`}
                    >
                      {row.mean_gain_pp > 0 ? "+" : ""}
                      {row.mean_gain_pp.toFixed(2)} pp
                    </td>
                    <td className="py-3">
                      [{row.ci_lower_pp.toFixed(2)},{" "}
                      {row.ci_upper_pp.toFixed(2)}] pp
                    </td>
                    <td className="py-3">{row.trials}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p className="mt-4 text-xs text-slate-500">
            Error bars represent 95% paired bootstrap confidence
            intervals. A confidence interval entirely above zero
            supports a positive interleaving effect; entirely below
            zero supports a negative effect. Intervals crossing zero
            are inconclusive at this confidence level.
          </p>
        </>
      )}
    </section>
  );
}
