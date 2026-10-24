"use client";

import { apiUrl } from "@/lib/api";
import { useState } from "react";
import PacketVisualizer from "@/components/PacketVisualizer";
import InterleavingComparison from "@/components/InterleavingComparison";
import SensorSignalChart from "@/components/SensorSignalChart";
import ExperimentalResults from "@/components/ExperimentalResults";
import InterleavingGain from "@/components/InterleavingGain";
import RecoveryOverhead from "@/components/RecoveryOverhead";
import SatelliteRecovery from "@/components/SatelliteRecovery";
import SatelliteResearch from "@/components/SatelliteResearch";

type SimulationRow = {
  method: string;
  source_packets: number;
  transmitted_packets: number;
  recovered_source_packets: number;
  source_packet_recovery_rate: number;
  transmission_loss_rate: number;
  encoding_seconds: number;
  decoding_seconds: number;
};

type SimulationResponse = {
  channel: string;
  seed: number;
  target_loss_rate: number;
  methods_evaluated: number;
  results: SimulationRow[];
};

export default function Home() {
  const [lossRate, setLossRate] = useState("0.25");
  const [seed, setSeed] = useState("42");
  const [data, setData] = useState<SimulationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState<
    "simulation" | "sensor" | "satellite" | "experiments" | "performance"
  >("simulation");

  async function runSimulation() {
    setLoading(true);
    setError("");
    setData(null);

    try {
      const response = await fetch(
        apiUrl("/api/simulate"),
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            seed: Number(seed),
            loss_rate: Number(lossRate),
          }),
        }
      );

      if (!response.ok) {
        const body = await response.json();
        throw new Error(JSON.stringify(body.detail ?? body));
      }

      const result: SimulationResponse = await response.json();
      setData(result);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Simulation failed."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-12 text-white">
      <div className="mx-auto max-w-6xl">
        <nav
          aria-label="Dashboard sections"
          className="mb-8 flex flex-wrap gap-3"
        >
          {[
            ["simulation", "Live Simulation"],
            ["sensor", "Sensor Recovery"],
            ["satellite", "Satellite Recovery"],
            ["experiments", "Experimental Results"],
            ["performance", "Performance Analysis"],
          ].map(([id, label]) => (
            <button
              key={id}
              type="button"
              onClick={() =>
                setActiveTab(
                  id as "simulation" | "sensor" | "satellite" | "experiments" | "performance"
                )
              }
              aria-current={activeTab === id ? "page" : undefined}
              className={`rounded-lg border px-4 py-2 text-sm font-medium transition ${
                activeTab === id
                  ? "border-cyan-400 bg-cyan-400/15 text-cyan-300"
                  : "border-slate-700 bg-slate-900 text-slate-300 hover:border-slate-500"
              }`}
            >
              {label}
            </button>
          ))}
        </nav>

        <p className="mb-3 text-sm font-semibold uppercase tracking-widest text-cyan-400">
          Sensor Communication Research
        </p>

        <h1 className="text-4xl font-bold tracking-tight">
          Hybrid Sensor Recovery
        </h1>

        <p className="mt-4 max-w-3xl text-slate-400">
          Interactive evaluation of exact sensor-packet recovery using
          Reed–Solomon coding, interleaving, and Fountain codes under
          burst packet loss.
        </p>

        {activeTab === "simulation" && (
          <>
        <section className="mt-10 rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <h2 className="text-xl font-semibold">Live Simulation</h2>

          <div className="mt-6 flex flex-wrap items-end gap-5">
            <label className="flex flex-col gap-2 text-sm text-slate-300">
              Target packet loss
              <select
                value={lossRate}
                onChange={(e) => setLossRate(e.target.value)}
                className="rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white"
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
                className="w-40 rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white"
              />
            </label>

            <button
              onClick={runSimulation}
              disabled={loading}
              className="rounded-lg bg-cyan-500 px-6 py-3 font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:opacity-50"
            >
              {loading ? "Running simulation..." : "Run Simulation"}
            </button>
          </div>

          {error && (
            <p role="alert" className="mt-5 text-sm text-red-400">
              {error}
            </p>
          )}
        </section>

        {data && (
          <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-6">
            <h2 className="text-xl font-semibold">
              Recovery Comparison
            </h2>

            <p className="mt-2 text-sm text-slate-400">
              {data.methods_evaluated} methods · Seed {data.seed} ·
              Target loss {data.target_loss_rate * 100}% ·
              Single simulation trial
            </p>

            <div className="mt-8 space-y-5">
              {data.results.map((row) => {
                const percentage =
                  row.source_packet_recovery_rate * 100;

                return (
                  <div key={row.method}>
                    <div className="mb-2 flex justify-between gap-4 text-sm">
                      <span className="text-slate-200">
                        {row.method}
                      </span>
                      <span className="font-semibold text-cyan-300">
                        {percentage.toFixed(2)}%
                      </span>
                    </div>

                    <div className="h-3 overflow-hidden rounded-full bg-slate-800">
                      <div
                        className="h-full rounded-full bg-cyan-400"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="mt-8 overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-slate-700 text-slate-400">
                  <tr>
                    <th className="py-3 pr-4">Method</th>
                    <th className="py-3 pr-4">Recovered packets</th>
                    <th className="py-3 pr-4">Transmitted</th>
                    <th className="py-3 pr-4">Encoding (ms)</th>
                    <th className="py-3">Decoding (ms)</th>
                  </tr>
                </thead>
                <tbody>
                  {data.results.map((row) => (
                    <tr
                      key={row.method}
                      className="border-b border-slate-800"
                    >
                      <td className="py-3 pr-4">{row.method}</td>
                      <td className="py-3 pr-4">
                        {row.recovered_source_packets}/
                        {row.source_packets}
                      </td>
                      <td className="py-3 pr-4">
                        {row.transmitted_packets}
                      </td>
                      <td className="py-3 pr-4">
                        {(row.encoding_seconds * 1000).toFixed(2)}
                      </td>
                      <td className="py-3">
                        {(row.decoding_seconds * 1000).toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}
          </>
        )}
        {activeTab === "simulation" && (
          <>
            <PacketVisualizer />
            <InterleavingComparison />
          </>
        )}

        {activeTab === "sensor" && <SensorSignalChart />}
        {activeTab === "satellite" && (
          <>
            <SatelliteRecovery />
            <SatelliteResearch />
          </>
        )}

        {activeTab === "experiments" && (
          <>
            <ExperimentalResults />
            <InterleavingGain />
          </>
        )}

        {activeTab === "performance" && <RecoveryOverhead />}
      </div>
    </main>
  );
}
