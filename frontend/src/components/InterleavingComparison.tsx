"use client";

import { apiUrl } from "@/lib/api";
import { useState } from "react";

type Status = "received" | "recovered" | "unrecovered";

type Trace = {
  method: string;
  source_packets: number;
  received_count: number;
  recovered_count: number;
  unrecovered_count: number;
  packet_statuses: Status[];
};

const colors: Record<Status, string> = {
  received: "bg-emerald-500",
  recovered: "bg-blue-500",
  unrecovered: "bg-rose-500",
};

export default function InterleavingComparison() {
  const [lossRate, setLossRate] = useState("0.25");
  const [seed, setSeed] = useState("42");
  const [parity, setParity] = useState("4");
  const [standard, setStandard] = useState<Trace | null>(null);
  const [interleaved, setInterleaved] = useState<Trace | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function compare() {
    setLoading(true);
    setError("");
    setStandard(null);
    setInterleaved(null);

    try {
      const request = {
        seed: Number(seed),
        loss_rate: Number(lossRate),
        parity_count: Number(parity),
      };

      const getTrace = async (enabled: boolean): Promise<Trace> => {
        const response = await fetch(
          apiUrl("/api/packet-trace"),
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              ...request,
              interleaved: enabled,
            }),
          }
        );

        if (!response.ok) {
          throw new Error(`Trace request failed: ${response.status}`);
        }

        return response.json();
      };

      const [rs, rsInterleaved] = await Promise.all([
        getTrace(false),
        getTrace(true),
      ]);

      setStandard(rs);
      setInterleaved(rsInterleaved);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Comparison failed.");
    } finally {
      setLoading(false);
    }
  }

  const recoveredTotal = (trace: Trace) =>
    trace.received_count + trace.recovered_count;

  const gain =
    standard && interleaved
      ? ((recoveredTotal(interleaved) - recoveredTotal(standard)) /
          standard.source_packets) *
        100
      : null;

  return (
    <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-6">
      <h2 className="text-xl font-semibold">
        Standard RS vs Interleaved RS
      </h2>

      <p className="mt-2 text-sm text-slate-400">
        Compare exact packet recovery under identical transmission-slot
        erasures. The same lost transmission positions affect different
        source packets after interleaving.
      </p>

      <div className="mt-6 flex flex-wrap items-end gap-4">
        <label className="flex flex-col gap-2 text-sm text-slate-300">
          Target loss
          <select
            value={lossRate}
            onChange={(e) => setLossRate(e.target.value)}
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
          >
            {[5, 10, 25, 50, 75].map((value) => (
              <option key={value} value={String(value / 100)}>
                {value}%
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-2 text-sm text-slate-300">
          Seed
          <input
            type="number"
            min="0"
            max="1000000"
            value={seed}
            onChange={(e) => setSeed(e.target.value)}
            className="w-32 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
          />
        </label>

        <label className="flex flex-col gap-2 text-sm text-slate-300">
          RS parity
          <select
            value={parity}
            onChange={(e) => setParity(e.target.value)}
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
          >
            <option value="2">8+2</option>
            <option value="4">8+4</option>
            <option value="8">8+8</option>
          </select>
        </label>

        <button
          onClick={compare}
          disabled={loading}
          className="rounded-lg bg-cyan-500 px-5 py-2 font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-50"
        >
          {loading ? "Comparing..." : "Compare Methods"}
        </button>
      </div>

      {error && <p role="alert" className="mt-4 text-red-400">{error}</p>}

      {standard && interleaved && (
        <>
          <div className="mt-8 grid gap-5 lg:grid-cols-2">
            {[standard, interleaved].map((trace) => {
              const recovered = recoveredTotal(trace);
              const percentage =
                (recovered / trace.source_packets) * 100;

              return (
                <div
                  key={trace.method}
                  className="rounded-xl border border-slate-700 bg-slate-950 p-5"
                >
                  <h3 className="font-semibold">{trace.method}</h3>

                  <p className="mt-3 text-3xl font-bold text-cyan-400">
                    {percentage.toFixed(2)}%
                  </p>

                  <p className="mt-1 text-sm text-slate-400">
                    {recovered}/{trace.source_packets} exactly recovered
                  </p>

                  <div className="mt-5 grid grid-cols-16 gap-1 sm:grid-cols-32 lg:grid-cols-16 xl:grid-cols-32">
                    {trace.packet_statuses.map((status, index) => (
                      <div
                        key={index}
                        title={`Packet ${index}: ${status}`}
                        className={`aspect-square rounded-sm ${colors[status]}`}
                      />
                    ))}
                  </div>

                  <div className="mt-4 flex flex-wrap gap-3 text-xs text-slate-400">
                    <span>Received: {trace.received_count}</span>
                    <span>Recovered: {trace.recovered_count}</span>
                    <span>Unrecovered: {trace.unrecovered_count}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {gain !== null && (
            <div className="mt-6 rounded-xl border border-slate-700 p-5">
              <p className="text-sm text-slate-400">
                Interleaving recovery difference
              </p>
              <p className="mt-2 text-3xl font-bold">
                {gain > 0 ? "+" : ""}
                {gain.toFixed(2)} percentage points
              </p>
              <p className="mt-2 text-sm text-slate-400">
                {gain > 0
                  ? "Interleaving recovered more packets in this trial."
                  : gain < 0
                    ? "Standard RS recovered more packets in this trial."
                    : "Both methods recovered the same number of packets."}
              </p>
            </div>
          )}

          <p className="mt-4 text-xs text-slate-500">
            Single-trial comparison. Interleaving does not guarantee
            improvement for every seed or loss condition.
          </p>
        </>
      )}
    </section>
  );
}
