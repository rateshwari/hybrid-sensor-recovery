"use client";

import { apiUrl } from "@/lib/api";
import { useState } from "react";

type PacketStatus = "received" | "recovered" | "unrecovered";

type PacketTrace = {
  method: string;
  seed: number;
  target_loss_rate: number;
  source_packets: number;
  transmitted_packets: number;
  received_count: number;
  recovered_count: number;
  unrecovered_count: number;
  packet_statuses: PacketStatus[];
};

const statusColors: Record<PacketStatus, string> = {
  received: "bg-emerald-500",
  recovered: "bg-blue-500",
  unrecovered: "bg-rose-500",
};

export default function PacketVisualizer() {
  const [lossRate, setLossRate] = useState("0.25");
  const [seed, setSeed] = useState("42");
  const [parity, setParity] = useState("4");
  const [interleaved, setInterleaved] = useState(true);

  const [trace, setTrace] = useState<PacketTrace | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadTrace() {
    setLoading(true);
    setError("");
    setTrace(null);

    try {
      const response = await fetch(
        apiUrl("/api/packet-trace"),
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            seed: Number(seed),
            loss_rate: Number(lossRate),
            parity_count: Number(parity),
            interleaved,
          }),
        }
      );

      if (!response.ok) {
        const body = await response.json();
        throw new Error(JSON.stringify(body.detail ?? body));
      }

      const result: PacketTrace = await response.json();
      setTrace(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-6">
      <h2 className="text-xl font-semibold">Packet Recovery Visualizer</h2>

      <p className="mt-2 text-sm text-slate-400">
        Explore the actual source-packet states after burst loss and
        Reed–Solomon decoding.
      </p>

      <div className="mt-6 flex flex-wrap items-end gap-4">
        <label className="flex flex-col gap-2 text-sm text-slate-300">
          Target packet loss
          <select
            value={lossRate}
            onChange={(e) => setLossRate(e.target.value)}
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
          >
            <option value="0.05">5%</option>
            <option value="0.10">10%</option>
            <option value="0.25">25%</option>
            <option value="0.50">50%</option>
            <option value="0.75">75%</option>
          </select>
        </label>

        <label className="flex flex-col gap-2 text-sm text-slate-300">
          Random seed
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

        <label className="flex items-center gap-2 pb-2 text-sm text-slate-300">
          <input
            type="checkbox"
            checked={interleaved}
            onChange={(e) => setInterleaved(e.target.checked)}
            className="h-4 w-4 accent-cyan-500"
          />
          Interleaving enabled
        </label>

        <button
          onClick={loadTrace}
          disabled={loading}
          className="rounded-lg bg-cyan-500 px-5 py-2 font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-50"
        >
          {loading ? "Loading..." : "Visualize Packets"}
        </button>
      </div>

      {error && (
        <p role="alert" className="mt-5 text-sm text-red-400">
          {error}
        </p>
      )}

      {trace && (
        <div className="mt-8">
          <h3 className="font-semibold">{trace.method}</h3>

          <p className="mt-1 text-sm text-slate-400">
            Seed {trace.seed} · Target loss{" "}
            {(trace.target_loss_rate * 100).toFixed(0)}% ·{" "}
            {trace.source_packets} source packets
          </p>

          <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-3">
            <div className="rounded-xl bg-slate-950 p-4">
              <p className="text-sm text-slate-400">Received</p>
              <p className="mt-1 text-2xl font-bold text-emerald-400">
                {trace.received_count}
              </p>
            </div>

            <div className="rounded-xl bg-slate-950 p-4">
              <p className="text-sm text-slate-400">Recovered by ECC</p>
              <p className="mt-1 text-2xl font-bold text-blue-400">
                {trace.recovered_count}
              </p>
            </div>

            <div className="rounded-xl bg-slate-950 p-4">
              <p className="text-sm text-slate-400">Unrecovered</p>
              <p className="mt-1 text-2xl font-bold text-rose-400">
                {trace.unrecovered_count}
              </p>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-8 gap-1 sm:grid-cols-16 md:grid-cols-32">
            {trace.packet_statuses.map((status, index) => (
              <div
                key={index}
                title={`Packet ${index}: ${status}`}
                aria-label={`Packet ${index}: ${status}`}
                className={`aspect-square rounded-sm ${statusColors[status]}`}
              />
            ))}
          </div>

          <div className="mt-5 flex flex-wrap gap-5 text-sm text-slate-300">
            <span>🟢 Received</span>
            <span>🔵 Recovered by ECC</span>
            <span>🔴 Unrecovered</span>
          </div>

          <p className="mt-4 text-xs text-slate-500">
            Each square represents one original source packet.
            Hover over a square to see its packet index and status.
          </p>
        </div>
      )}
    </section>
  );
}
