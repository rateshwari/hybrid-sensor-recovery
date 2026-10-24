"use client";

import { apiUrl } from "@/lib/api";
import { useEffect, useState } from "react";

type Metric =
  | "redundancy_percent"
  | "encoding_ms"
  | "decoding_ms"
  | "encoding_memory_kib"
  | "decoding_memory_kib";

type PerformanceRow = {
  method: string;
  target_loss_rate: number;
  trials: number;
  recovery_percent: number;
  redundancy_percent: number;
  encoding_ms: number;
  decoding_ms: number;
  encoding_memory_kib: number;
  decoding_memory_kib: number;
};

type PerformanceResponse = {
  channel: string;
  methods: string[];
  loss_rates: number[];
  results: PerformanceRow[];
};

const METRICS: Record<Metric, { label: string; unit: string }> = {
  redundancy_percent: { label: "Redundancy", unit: "%" },
  encoding_ms: { label: "Encoding time", unit: "ms" },
  decoding_ms: { label: "Decoding time", unit: "ms" },
  encoding_memory_kib: { label: "Encoding memory", unit: "KiB" },
  decoding_memory_kib: { label: "Decoding memory", unit: "KiB" },
};

const WIDTH = 900;
const HEIGHT = 390;
const LEFT = 70;
const RIGHT = 35;
const TOP = 25;
const BOTTOM = 65;

const COLORS = [
  "#22d3ee", "#34d399", "#fbbf24", "#f472b6", "#a78bfa",
  "#fb7185", "#60a5fa", "#f97316", "#c084fc", "#2dd4bf",
];

export default function RecoveryOverhead() {
  const [data, setData] = useState<PerformanceResponse | null>(null);
  const [loss, setLoss] = useState(0.25);
  const [metric, setMetric] = useState<Metric>("redundancy_percent");
  const [selectedMethods, setSelectedMethods] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      try {
        const response = await fetch(
          apiUrl("/api/performance-comparison"),
          { signal: controller.signal }
        );

        if (!response.ok) {
          throw new Error(`API returned ${response.status}`);
        }

        const result: PerformanceResponse = await response.json();

        if (!controller.signal.aborted) {
          setData(result);
          setSelectedMethods(result.methods);
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(
            err instanceof Error ? err.message : "Unable to load performance data"
          );
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    load();
    return () => controller.abort();
  }, []);

  const rows = (data?.results ?? [])
    .filter(
      (row) =>
        Math.abs(row.target_loss_rate - loss) < 1e-9 &&
        selectedMethods.includes(row.method)
    );

  const maxValue = Math.max(
    1,
    ...rows.map((row) => row[metric])
  );

  const plotWidth = WIDTH - LEFT - RIGHT;
  const plotHeight = HEIGHT - TOP - BOTTOM;

  const x = (value: number) =>
    LEFT + (value / (maxValue * 1.1)) * plotWidth;

  const y = (recovery: number) =>
    TOP + ((100 - recovery) / 100) * plotHeight;

  const toggleMethod = (method: string) => {
    setSelectedMethods((previous) =>
      previous.includes(method)
        ? previous.filter((item) => item !== method)
        : [...previous, method]
    );
  };

  const metricInfo = METRICS[metric];

  return (
    <section className="mt-10 rounded-2xl border border-slate-700 bg-slate-800/60 p-6">
      <h2 className="text-2xl font-bold text-cyan-400">
        Recovery vs. Computational Overhead
      </h2>

      <p className="mt-2 text-sm text-slate-400">
        Explore how exact packet recovery changes with coding redundancy,
        execution time, and memory consumption under Gilbert–Elliott
        burst loss. Each point represents an aggregated experimental
        configuration.
      </p>

      <div className="mt-6 flex flex-wrap gap-4">
        <label className="text-sm text-slate-300">
          Target loss
          <select
            value={loss}
            onChange={(e) => setLoss(Number(e.target.value))}
            className="ml-3 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-white"
          >
            {[0.05, 0.1, 0.25, 0.5, 0.75].map((value) => (
              <option key={value} value={value}>
                {(value * 100).toFixed(0)}%
              </option>
            ))}
          </select>
        </label>

        <label className="text-sm text-slate-300">
          Overhead metric
          <select
            value={metric}
            onChange={(e) => setMetric(e.target.value as Metric)}
            className="ml-3 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-white"
          >
            {(Object.keys(METRICS) as Metric[]).map((key) => (
              <option key={key} value={key}>
                {METRICS[key].label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {loading && (
        <p className="mt-5 text-cyan-300">Loading performance results...</p>
      )}

      {error && <p className="mt-5 text-red-400">{error}</p>}

      {data && (
        <>
          <div className="mt-6 flex flex-wrap gap-3">
            {data.methods.map((method, index) => (
              <label
                key={method}
                className="flex cursor-pointer items-center gap-2 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-slate-200"
              >
                <input
                  type="checkbox"
                  checked={selectedMethods.includes(method)}
                  onChange={() => toggleMethod(method)}
                  style={{ accentColor: COLORS[index % COLORS.length] }}
                />
                {method}
              </label>
            ))}
          </div>

          <div className="mt-6 overflow-x-auto rounded-xl bg-slate-950 p-3">
            <svg
              viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
              className="min-w-[650px] w-full"
              role="img"
              aria-label={`Recovery percentage versus ${metricInfo.label}`}
            >
              {[0, 25, 50, 75, 100].map((tick) => (
                <g key={tick}>
                  <line
                    x1={LEFT}
                    y1={y(tick)}
                    x2={WIDTH - RIGHT}
                    y2={y(tick)}
                    stroke="#334155"
                    strokeDasharray="4 4"
                  />
                  <text
                    x={LEFT - 12}
                    y={y(tick) + 4}
                    textAnchor="end"
                    fill="#94a3b8"
                    fontSize="12"
                  >
                    {tick}%
                  </text>
                </g>
              ))}

              {[0, 0.25, 0.5, 0.75, 1].map((fraction) => (
                <text
                  key={fraction}
                  x={LEFT + (fraction / 1.1) * plotWidth}
                  y={HEIGHT - 36}
                  fill="#94a3b8"
                  fontSize="12"
                  textAnchor="middle"
                >
                  {(maxValue * fraction).toFixed(
                    metric === "redundancy_percent" ? 0 : 1
                  )}
                </text>
              ))}

              {rows.map((row) => {
                const index = data.methods.indexOf(row.method);
                const color = COLORS[index % COLORS.length];

                return (
                  <circle
                    key={row.method}
                    cx={x(row[metric])}
                    cy={y(row.recovery_percent)}
                    r="7"
                    fill={color}
                    stroke="#020617"
                    strokeWidth="2"
                  >
                    <title>
                      {row.method}: {row.recovery_percent.toFixed(2)}%
                      recovery, {row[metric].toFixed(2)} {metricInfo.unit}
                    </title>
                  </circle>
                );
              })}

              <text
                x={WIDTH / 2}
                y={HEIGHT - 7}
                textAnchor="middle"
                fill="#94a3b8"
                fontSize="13"
              >
                {metricInfo.label} ({metricInfo.unit})
              </text>
            </svg>
          </div>

          <div className="mt-7 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-700 text-slate-400">
                <tr>
                  <th className="py-3">Method</th>
                  <th className="py-3">Recovery</th>
                  <th className="py-3">
                    {metricInfo.label} ({metricInfo.unit})
                  </th>
                  <th className="py-3">Trials</th>
                </tr>
              </thead>
              <tbody>
                {[...rows]
                  .sort((a, b) => b.recovery_percent - a.recovery_percent)
                  .map((row) => (
                    <tr
                      key={row.method}
                      className="border-b border-slate-800 text-slate-200"
                    >
                      <td className="py-3 pr-4">{row.method}</td>
                      <td className="py-3">
                        {row.recovery_percent.toFixed(2)}%
                      </td>
                      <td className="py-3">
                        {row[metric].toFixed(2)}
                      </td>
                      <td className="py-3">{row.trials}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>

          <p className="mt-4 text-xs text-slate-500">
            Recovery is averaged across 30 burst-channel trials.
            Timing and memory measurements come from the recorded
            performance experiments. Lower overhead is generally
            preferable when recovery performance is comparable.
          </p>
        </>
      )}
    </section>
  );
}
