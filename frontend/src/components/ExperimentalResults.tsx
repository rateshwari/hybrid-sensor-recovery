"use client";

import { apiUrl } from "@/lib/api";
import { useEffect, useState } from "react";

type Channel = "iid" | "burst";

type Result = {
  method: string;
  loss_rate: number;
  trials: number;
  mean_recovery_percent: number;
  std_recovery_pp: number;
  confidence_interval: {
    ci_lower: number;
    ci_upper: number;
  } | null;
};

type ResultsResponse = {
  channel: Channel;
  total_trials: number;
  methods: string[];
  loss_rates: number[];
  results: Result[];
};

const WIDTH = 900;
const HEIGHT = 350;
const LEFT = 60;
const RIGHT = 25;
const TOP = 25;
const BOTTOM = 55;

const COLORS = [
  "#22d3ee",
  "#34d399",
  "#fbbf24",
  "#f472b6",
  "#a78bfa",
  "#fb7185",
  "#60a5fa",
  "#f97316",
  "#c084fc",
  "#2dd4bf",
];

export default function ExperimentalResults() {
  const [channel, setChannel] = useState<Channel>("burst");
  const [data, setData] = useState<ResultsResponse | null>(null);
  const [selectedMethods, setSelectedMethods] = useState<string[]>([]);
  const [selectedLoss, setSelectedLoss] = useState(0.25);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      setLoading(true);
      setError("");
      setData(null);

      try {
        const response = await fetch(
          apiUrl(`/api/experimental-results?channel=${channel}`),
          { signal: controller.signal }
        );

        if (!response.ok) {
          throw new Error(`Results API returned ${response.status}`);
        }

        const result: ResultsResponse = await response.json();
        setData(result);

        setSelectedMethods((previous) => {
          const retained = previous.filter((method) =>
            result.methods.includes(method)
          );

          return retained.length
            ? retained
            : result.methods.slice(0, 5);
        });
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(
            err instanceof Error ? err.message : "Unable to load results"
          );
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    load();

    return () => controller.abort();
  }, [channel]);

  const plotWidth = WIDTH - LEFT - RIGHT;
  const plotHeight = HEIGHT - TOP - BOTTOM;

  const x = (loss: number) =>
    LEFT + ((loss - 0.05) / 0.7) * plotWidth;

  const y = (recovery: number) =>
    TOP + ((100 - recovery) / 100) * plotHeight;

  const toggleMethod = (method: string) => {
    setSelectedMethods((previous) =>
      previous.includes(method)
        ? previous.filter((item) => item !== method)
        : [...previous, method]
    );
  };

  const tableRows = (data?.results ?? [])
    .filter(
      (result) =>
        Math.abs(result.loss_rate - selectedLoss) < 1e-9 &&
        selectedMethods.includes(result.method)
    )
    .sort(
      (a, b) =>
        b.mean_recovery_percent - a.mean_recovery_percent
    );

  return (
    <section className="mt-10 rounded-2xl border border-slate-700 bg-slate-800/60 p-6">
      <h2 className="text-2xl font-bold text-cyan-400">
        Experimental Recovery Results
      </h2>

      <p className="mt-2 text-sm text-slate-400">
        Compare mean exact source-packet recovery across 30 trials
        per configuration. These are completed research experiments,
        not single-run simulations.
      </p>

      <div className="mt-6 flex flex-wrap items-center gap-4">
        <label className="text-sm text-slate-300">
          Channel model
          <select
            value={channel}
            onChange={(e) => setChannel(e.target.value as Channel)}
            className="ml-3 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-white"
          >
            <option value="burst">Gilbert–Elliott Burst</option>
            <option value="iid">IID Random Loss</option>
          </select>
        </label>

        {data && (
          <span className="text-sm text-slate-400">
            {data.total_trials.toLocaleString()} trial records ·{" "}
            {data.methods.length} methods
          </span>
        )}
      </div>

      {loading && (
        <p className="mt-5 text-cyan-300">Loading experimental results...</p>
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
              aria-label="Mean exact recovery percentage by target packet loss"
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
                    x={LEFT - 10}
                    y={y(tick) + 4}
                    fill="#94a3b8"
                    fontSize="12"
                    textAnchor="end"
                  >
                    {tick}%
                  </text>
                </g>
              ))}

              {data.loss_rates.map((loss) => (
                <g key={loss}>
                  <text
                    x={x(loss)}
                    y={HEIGHT - 30}
                    fill="#94a3b8"
                    fontSize="12"
                    textAnchor="middle"
                  >
                    {(loss * 100).toFixed(0)}%
                  </text>
                </g>
              ))}

              {data.methods
                .filter((method) => selectedMethods.includes(method))
                .map((method) => {
                  const methodResults = data.results
                    .filter((result) => result.method === method)
                    .sort((a, b) => a.loss_rate - b.loss_rate);

                  const color =
                    COLORS[data.methods.indexOf(method) % COLORS.length];

                  const path = methodResults
                    .map(
                      (result, index) =>
                        `${index === 0 ? "M" : "L"} ${x(
                          result.loss_rate
                        )} ${y(result.mean_recovery_percent)}`
                    )
                    .join(" ");

                  return (
                    <g key={method}>
                      <path
                        d={path}
                        fill="none"
                        stroke={color}
                        strokeWidth="2.5"
                      />

                      {methodResults.map((result) => (
                        <circle
                          key={result.loss_rate}
                          cx={x(result.loss_rate)}
                          cy={y(result.mean_recovery_percent)}
                          r="4"
                          fill={color}
                        >
                          <title>
                            {method}:{" "}
                            {result.mean_recovery_percent.toFixed(2)}%
                            recovery at{" "}
                            {(result.loss_rate * 100).toFixed(0)}%
                            target loss
                          </title>
                        </circle>
                      ))}
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
                Target packet loss rate
              </text>
            </svg>
          </div>

          <div className="mt-7 flex flex-wrap items-center gap-4">
            <h3 className="text-lg font-semibold text-white">
              Detailed Comparison
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
                  <th className="py-3">Method</th>
                  <th className="py-3">Mean recovery</th>
                  <th className="py-3">Std. deviation</th>
                  <th className="py-3">95% Bootstrap CI</th>
                  <th className="py-3">Trials</th>
                </tr>
              </thead>

              <tbody>
                {tableRows.map((result) => (
                  <tr
                    key={result.method}
                    className="border-b border-slate-800 text-slate-200"
                  >
                    <td className="py-3 pr-4">{result.method}</td>
                    <td className="py-3">
                      {result.mean_recovery_percent.toFixed(2)}%
                    </td>
                    <td className="py-3">
                      ±{result.std_recovery_pp.toFixed(2)} pp
                    </td>
                    <td className="py-3">
                      {result.confidence_interval
                        ? `${result.confidence_interval.ci_lower.toFixed(2)}%–${result.confidence_interval.ci_upper.toFixed(2)}%`
                        : "Not available"}
                    </td>
                    <td className="py-3">{result.trials}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p className="mt-4 text-xs text-slate-500">
            Standard deviation describes trial-to-trial variation;
            it is not a confidence interval. Only methods actually
            evaluated for the selected channel are displayed.
          </p>
        </>
      )}
    </section>
  );
}
