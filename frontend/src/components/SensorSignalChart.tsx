"use client";

import { apiUrl } from "@/lib/api";
import { useEffect, useState } from "react";

type Signal = "temperature" | "humidity";

type Point = {
  reading_index: number;
  timestamp: string;
  packet_index: number;
  packet_status: "received" | "recovered" | "unrecovered";
  original: number;
  available_after_recovery: number | null;
};

type SignalResponse = {
  method: string;
  signal: Signal;
  seed: number;
  target_loss_rate: number;
  start: number;
  count: number;
  total_readings: number;
  points: Point[];
};

const CHART_WIDTH = 900;
const CHART_HEIGHT = 300;
const LEFT = 58;
const RIGHT = 20;
const TOP = 22;
const BOTTOM = 42;

export default function SensorSignalChart() {
  const [signal, setSignal] = useState<Signal>("temperature");
  const [lossRate, setLossRate] = useState(25);
  const [seed, setSeed] = useState(42);
  const [parity, setParity] = useState(4);
  const [interleaved, setInterleaved] = useState(true);
  const [start, setStart] = useState(2048);
  const [data, setData] = useState<SignalResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      setLoading(true);
      setError("");
      setData(null);

      try {
        const response = await fetch(
          apiUrl("/api/sensor-signal"),
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              seed,
              loss_rate: lossRate / 100,
              parity_count: parity,
              interleaved,
              signal,
              start,
              count: 512,
            }),
            signal: controller.signal,
          }
        );

        if (!response.ok) {
          throw new Error(`Sensor API returned ${response.status}`);
        }

        const result: SignalResponse = await response.json();
        setData(result);
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(
            err instanceof Error ? err.message : "Unable to load sensor data"
          );
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    load();
    return () => controller.abort();
  }, [signal, lossRate, seed, parity, interleaved, start]);

  const points = data?.points ?? [];
  const plotWidth = CHART_WIDTH - LEFT - RIGHT;
  const plotHeight = CHART_HEIGHT - TOP - BOTTOM;

  const values = points.map((p) => p.original);
  const rawMin = values.length ? Math.min(...values) : 0;
  const rawMax = values.length ? Math.max(...values) : 1;
  const margin = Math.max((rawMax - rawMin) * 0.12, 0.01);
  const minY = rawMin - margin;
  const maxY = rawMax + margin;

  const x = (i: number) =>
    LEFT + (i / Math.max(points.length - 1, 1)) * plotWidth;

  const y = (value: number) =>
    TOP + ((maxY - value) / (maxY - minY)) * plotHeight;

  const hoveredPoint =
    hoverIndex !== null ? points[hoverIndex] ?? null : null;

  const handleChartMouseMove = (
    event: React.MouseEvent<SVGSVGElement>
  ) => {
    if (points.length === 0) return;

    const svg = event.currentTarget;
    const bounds = svg.getBoundingClientRect();
    const scaleX = CHART_WIDTH / bounds.width;
    const mouseX = (event.clientX - bounds.left) * scaleX;

    if (mouseX < LEFT || mouseX > CHART_WIDTH - RIGHT) {
      setHoverIndex(null);
      return;
    }

    const index = Math.round(
      ((mouseX - LEFT) / plotWidth) * (points.length - 1)
    );

    setHoverIndex(Math.max(0, Math.min(index, points.length - 1)));
  };

  const originalPath = points
    .map((p, i) => `${i === 0 ? "M" : "L"} ${x(i)} ${y(p.original)}`)
    .join(" ");

  // Start a new path whenever a reading is unavailable.
  // This prevents the recovered line from crossing missing-data gaps.
  let recoveredPath = "";
  let previousAvailable = false;

  points.forEach((p, i) => {
    const value = p.available_after_recovery;
    if (value === null) {
      previousAvailable = false;
      return;
    }

    recoveredPath += `${
      previousAvailable ? " L" : " M"
    } ${x(i)} ${y(value)}`;

    previousAvailable = true;
  });

  const missingCount = points.filter(
    (p) => p.available_after_recovery === null
  ).length;

  const recoveredCount = points.filter(
    (p) => p.packet_status === "recovered"
  ).length;

  const inputClass =
    "rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white";

  return (
    <section className="mt-10 rounded-2xl border border-slate-700 bg-slate-800/60 p-6">
      <h2 className="text-2xl font-bold text-cyan-400">
        Sensor Signal Recovery
      </h2>

      <p className="mt-2 text-sm text-slate-400">
        Compare original sensor readings with readings available after
        exact packet recovery. Missing packets create gaps, not
        reconstructed or interpolated values.
      </p>

      <div className="mt-6 flex flex-wrap items-end gap-4">
        <label className="flex flex-col gap-2 text-sm text-slate-300">
          Signal
          <select
            className={inputClass}
            value={signal}
            onChange={(e) => setSignal(e.target.value as Signal)}
          >
            <option value="temperature">Temperature</option>
            <option value="humidity">Humidity</option>
          </select>
        </label>

        <label className="flex flex-col gap-2 text-sm text-slate-300">
          Target loss
          <select
            className={inputClass}
            value={lossRate}
            onChange={(e) => setLossRate(Number(e.target.value))}
          >
            {[5, 10, 25, 50, 75].map((value) => (
              <option key={value} value={value}>
                {value}%
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-2 text-sm text-slate-300">
          Parity packets
          <select
            className={inputClass}
            value={parity}
            onChange={(e) => setParity(Number(e.target.value))}
          >
            {[2, 4, 8].map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-2 text-sm text-slate-300">
          Seed
          <input
            type="number"
            min={0}
            max={1000000}
            className={`${inputClass} w-28`}
            value={seed}
            onChange={(e) => setSeed(Number(e.target.value))}
          />
        </label>

        <label className="flex items-center gap-2 pb-2 text-sm text-slate-300">
          <input
            type="checkbox"
            checked={interleaved}
            onChange={(e) => setInterleaved(e.target.checked)}
            className="accent-cyan-400"
          />
          Interleaving
        </label>
      </div>

      <div className="mt-5">
        <div className="mb-2 flex justify-between text-sm text-slate-300">
          <span>Starting reading: {start.toLocaleString()}</span>
          <span>
            Window: {start.toLocaleString()}–
            {Math.min(start + 511, 16325).toLocaleString()}
          </span>
        </div>

        <input
          type="range"
          min={0}
          max={15814}
          step={64}
          value={start}
          onChange={(e) => setStart(Number(e.target.value))}
          className="w-full accent-cyan-400"
        />
      </div>

      {loading && (
        <p className="mt-6 text-sm text-cyan-300">
          Loading sensor recovery data...
        </p>
      )}

      {error && (
        <p className="mt-6 text-sm text-red-400">{error}</p>
      )}

      {data && points.length > 0 && (
        <>
          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            <div className="rounded-xl bg-slate-900 p-4">
              <p className="text-xs text-slate-400">Readings displayed</p>
              <p className="mt-1 text-2xl font-semibold text-white">
                {points.length}
              </p>
            </div>

            <div className="rounded-xl bg-slate-900 p-4">
              <p className="text-xs text-slate-400">
                Readings restored by ECC
              </p>
              <p className="mt-1 text-2xl font-semibold text-blue-400">
                {recoveredCount}
              </p>
            </div>

            <div className="rounded-xl bg-slate-900 p-4">
              <p className="text-xs text-slate-400">Unavailable readings</p>
              <p className="mt-1 text-2xl font-semibold text-red-400">
                {missingCount}
              </p>
            </div>
          </div>

          <p className="mt-5 text-sm text-slate-300">
            Method: <strong>{data.method}</strong>
          </p>

          <div className="mt-4 overflow-x-auto rounded-xl bg-slate-950 p-3">
            <svg
              onMouseMove={handleChartMouseMove}
              onMouseLeave={() => setHoverIndex(null)}
              viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
              className="min-w-[650px] w-full"
              role="img"
              aria-label={`${signal} sensor readings before and after packet recovery`}
            >
              {[0, 1, 2, 3, 4].map((tick) => {
                const value = minY + ((maxY - minY) * tick) / 4;
                const yy = y(value);

                return (
                  <g key={tick}>
                    <line
                      x1={LEFT}
                      y1={yy}
                      x2={CHART_WIDTH - RIGHT}
                      y2={yy}
                      stroke="#334155"
                      strokeDasharray="4 4"
                    />
                    <text
                      x={LEFT - 8}
                      y={yy + 4}
                      textAnchor="end"
                      fill="#94a3b8"
                      fontSize="11"
                    >
                      {value.toFixed(2)}
                    </text>
                  </g>
                );
              })}

              {points.map((point, index) => {
  if (point.packet_status !== "unrecovered") {
    return null;
  }

  const previousMissing =
    index > 0 &&
    points[index - 1].packet_status === "unrecovered";

  if (previousMissing) {
    return null;
  }

  let endIndex = index;

  while (
    endIndex + 1 < points.length &&
    points[endIndex + 1].packet_status === "unrecovered"
  ) {
    endIndex++;
  }

  const startX = index === 0 ? LEFT : (x(index - 1) + x(index)) / 2;

  const endX =
    endIndex === points.length - 1
      ? CHART_WIDTH - RIGHT
      : (x(endIndex) + x(endIndex + 1)) / 2;

  return (
    <rect
      key={`missing-${point.packet_index}-${index}`}
      x={startX}
      y={TOP}
      width={endX - startX}
      height={plotHeight}
      fill="#ef4444"
      fillOpacity="0.14"
    >
      <title>
        Unavailable sensor readings:
        {" "}
        {point.reading_index}–
        {points[endIndex].reading_index}
      </title>
    </rect>
  );
})}

              <path
                d={originalPath}
                fill="none"
                stroke="#34d399"
                strokeWidth="2"
                opacity="0.75"
              />

              <path
                d={recoveredPath}
                fill="none"
                stroke="#38bdf8"
                strokeWidth="2"
                strokeLinecap="round"
              />

              <text
                x={CHART_WIDTH / 2}
                y={CHART_HEIGHT - 8}
                textAnchor="middle"
                fill="#94a3b8"
                fontSize="12"
              >
                Sensor reading index
              </text>

              <text
                x={LEFT}
                y={CHART_HEIGHT - 27}
                fill="#94a3b8"
                fontSize="11"
              >
                {points[0].reading_index}
              </text>

              <text
                x={CHART_WIDTH - RIGHT}
                y={CHART_HEIGHT - 27}
                textAnchor="end"
                fill="#94a3b8"
                fontSize="11"
              >
                {points[points.length - 1].reading_index}
              </text>
              {hoveredPoint && hoverIndex !== null && (
                <g pointerEvents="none">
                  <line
                    x1={x(hoverIndex)}
                    y1={TOP}
                    x2={x(hoverIndex)}
                    y2={CHART_HEIGHT - BOTTOM}
                    stroke="#f8fafc"
                    strokeDasharray="4 4"
                    opacity="0.65"
                  />
                  <circle
                    cx={x(hoverIndex)}
                    cy={y(hoveredPoint.original)}
                    r="4"
                    fill="#f8fafc"
                    stroke="#0f172a"
                    strokeWidth="2"
                  />
                </g>
              )}
            </svg>
          </div>

          {hoveredPoint && (
            <div className="mt-4 rounded-xl border border-slate-700 bg-slate-900 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h3 className="font-semibold text-white">
                  Sensor Reading #{hoveredPoint.reading_index}
                </h3>
                <span
                  className={`rounded-full px-3 py-1 text-xs font-semibold ${
                    hoveredPoint.packet_status === "received"
                      ? "bg-emerald-500/15 text-emerald-400"
                      : hoveredPoint.packet_status === "recovered"
                      ? "bg-sky-500/15 text-sky-400"
                      : "bg-red-500/15 text-red-400"
                  }`}
                >
                  {hoveredPoint.packet_status.toUpperCase()}
                </span>
              </div>

              <div className="mt-3 grid gap-3 text-sm sm:grid-cols-2">
                <p className="text-slate-300">
                  Timestamp: <strong>{hoveredPoint.timestamp}</strong>
                </p>
                <p className="text-slate-300">
                  Source packet: <strong>{hoveredPoint.packet_index}</strong>
                </p>
                <p className="text-slate-300">
                  Original {signal}:{" "}
                  <strong>{hoveredPoint.original.toFixed(4)}</strong>
                </p>
                <p className="text-slate-300">
                  Available after recovery:{" "}
                  <strong>
                    {hoveredPoint.available_after_recovery === null
                      ? "Unavailable"
                      : hoveredPoint.available_after_recovery.toFixed(4)}
                  </strong>
                </p>
              </div>
            </div>
          )}

          <div className="mt-4 flex flex-wrap gap-5 text-sm">
            <span className="text-emerald-400">● Original signal</span>
            <span className="text-sky-400">
              ● Available after recovery
            </span>
            <span className="text-red-400">
              ● Gaps indicate unavailable readings
            </span>
          </div>

          <p className="mt-3 text-xs text-slate-500">
            Values shown are the original dataset measurements at
            available packet positions. This is a packet-availability
            visualization, not a decoded quantization-error comparison.
          </p>
        </>
      )}
    </section>
  );
}
