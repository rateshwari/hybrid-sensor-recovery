"use client";

import { useEffect, useMemo, useState } from "react";
import { apiUrl } from "@/lib/api";

type PacketRow = {
  channel: string;
  target_loss_rate: number;
  method: string;
  n: number;
  mean: number;
  ci_lower: number;
  ci_upper: number;
};

type QualityRow = {
  channel: string;
  method: string;
  observations: number;
  mean_ssim: number;
  exact_image_recovery_percent: number;
};

type ClassRow = {
  channel: string;
  class_name: string;
  method: string;
  observations: number;
  mean_ssim: number;
};

type InterleavingRow = {
  channel: string;
  target_loss_rate: number;
  parity: number;
  n: number;
  mean: number;
  ci_lower: number;
  ci_upper: number;
};

type SSIMInterleavingRow = {
  channel: string;
  parity: number;
  seeds: number;
  mean_ssim_gain: number;
  ci_lower: number;
  ci_upper: number;
};

type ResearchData = {
  metadata: {
    images: number;
    channel_seeds: number;
    packet_benchmark_trials: number;
    image_quality_observations: number;
  };
  packet_recovery: PacketRow[];
  packet_interleaving: InterleavingRow[];
  method_quality: QualityRow[];
  class_quality: ClassRow[];
  ssim_interleaving: SSIMInterleavingRow[];
};

const METHODS = [
  "No ECC",
  "RS (8+2)",
  "RS (8+4)",
  "RS (8+8)",
  "RS Interleaved (8+2)",
  "RS Interleaved (8+4)",
  "RS Interleaved (8+8)",
  "Fountain (1.25x)",
  "Fountain (1.50x)",
  "Fountain (2.00x)",
];

const LOSSES = [0.05, 0.1, 0.25, 0.5, 0.75];

const selectStyle =
  "rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white";

export default function SatelliteResearch() {
  const [data, setData] = useState<ResearchData | null>(null);
  const [channel, setChannel] = useState("burst");
  const [lossRate, setLossRate] = useState(0.25);
  const [method, setMethod] = useState("RS Interleaved (8+4)");
  const [className, setClassName] = useState("All classes");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const response = await fetch(
          apiUrl("/api/satellite/research-results")
        );

        if (!response.ok) {
          throw new Error("Could not load satellite research results.");
        }

        const result: ResearchData = await response.json();

        if (!cancelled) setData(result);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Research loading failed."
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, []);

  const classes = useMemo(() => {
    if (!data) return [];

    return Array.from(
      new Set(data.class_quality.map((row) => row.class_name))
    ).sort();
  }, [data]);

  if (loading) {
    return (
      <p className="mt-8 text-slate-400">
        Loading satellite research results...
      </p>
    );
  }

  if (error || !data) {
    return (
      <p role="alert" className="mt-8 text-red-400">
        {error || "Research data unavailable."}
      </p>
    );
  }

  const packetRows = data.packet_recovery.filter(
    (row) =>
      row.channel === channel &&
      Math.abs(row.target_loss_rate - lossRate) < 1e-9
  );

  const qualityRows = data.method_quality.filter(
    (row) => row.channel === channel
  );

  const classRows = data.class_quality
    .filter(
      (row) =>
        row.channel === channel &&
        row.method === method &&
        (className === "All classes" ||
          row.class_name === className)
    )
    .sort((a, b) => b.mean_ssim - a.mean_ssim);

  const packetInterleaving = data.packet_interleaving
    .filter(
      (row) =>
        row.channel === channel &&
        Math.abs(row.target_loss_rate - lossRate) < 1e-9
    )
    .sort((a, b) => a.parity - b.parity);

  const ssimInterleaving = data.ssim_interleaving
    .filter((row) => row.channel === channel)
    .sort((a, b) => a.parity - b.parity);

  return (
    <section className="mt-10 space-y-6">
      <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="text-2xl font-bold">
          Satellite Research Results
        </h2>

        <p className="mt-2 text-sm text-slate-400">
          Precomputed EuroSAT experiments across 500 images,
          30 channel seeds, ten coding methods, and two channel models.
        </p>

        <div className="mt-6 flex flex-wrap gap-5">
          <label className="flex flex-col gap-2 text-sm text-slate-300">
            Channel model
            <select
              className={selectStyle}
              value={channel}
              onChange={(e) => setChannel(e.target.value)}
            >
              <option value="iid">IID random loss</option>
              <option value="burst">Gilbert–Elliott burst loss</option>
            </select>
          </label>

          <label className="flex flex-col gap-2 text-sm text-slate-300">
            Target packet loss
            <select
              className={selectStyle}
              value={lossRate}
              onChange={(e) => setLossRate(Number(e.target.value))}
            >
              {LOSSES.map((loss) => (
                <option key={loss} value={loss}>
                  {loss * 100}%
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-2 text-sm text-slate-300">
            Recovery method (class analysis)
            <select
              className={selectStyle}
              value={method}
              onChange={(e) => setMethod(e.target.value)}
            >
              {METHODS.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-2 text-sm text-slate-300">
            Land-use class
            <select
              className={selectStyle}
              value={className}
              onChange={(e) => setClassName(e.target.value)}
            >
              <option>All classes</option>
              {classes.map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
          </label>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <h3 className="text-xl font-semibold">
          Packet Recovery Comparison
        </h3>
        <p className="mt-2 text-sm text-slate-400">
          Mean byte-exact source-packet recovery across 30 seeds.
          Error ranges are 95% confidence intervals.
        </p>

        <div className="mt-6 space-y-5">
          {METHODS.map((name) => {
            const row = packetRows.find((r) => r.method === name);
            if (!row) return null;

            return (
              <div key={name}>
                <div className="mb-2 flex justify-between gap-4 text-sm">
                  <span className="text-slate-200">{name}</span>
                  <span className="font-semibold text-cyan-300">
                    {row.mean.toFixed(2)}%
                  </span>
                </div>

                <div className="h-3 overflow-hidden rounded-full bg-slate-800">
                  <div
                    className="h-full rounded-full bg-cyan-400"
                    style={{
                      width: `${Math.max(
                        0,
                        Math.min(100, row.mean)
                      )}%`,
                    }}
                  />
                </div>

                <p className="mt-1 text-xs text-slate-500">
                  95% CI [{row.ci_lower.toFixed(2)}%,{" "}
                  {row.ci_upper.toFixed(2)}%]
                </p>
              </div>
            );
          })}
        </div>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <h3 className="text-xl font-semibold">
          Satellite Image Quality
        </h3>

        <p className="mt-2 text-sm text-slate-400">
          Mean SSIM and exact-image recovery at 25% target packet
          loss, across 500 images and 30 seeds.
          These values do not change with the packet-loss selector.
        </p>

        <div className="mt-6 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-700 text-slate-400">
              <tr>
                <th className="py-3 pr-4">Method</th>
                <th className="py-3 pr-4">Mean SSIM</th>
                <th className="py-3">Exact images</th>
              </tr>
            </thead>
            <tbody>
              {METHODS.map((name) => {
                const row = qualityRows.find((r) => r.method === name);
                if (!row) return null;

                return (
                  <tr
                    key={name}
                    className="border-b border-slate-800"
                  >
                    <td className="py-3 pr-4">{name}</td>
                    <td className="py-3 pr-4 text-cyan-300">
                      {row.mean_ssim.toFixed(4)}
                    </td>
                    <td className="py-3">
                      {row.exact_image_recovery_percent.toFixed(2)}%
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <h3 className="text-xl font-semibold">
          Land-Use Class Analysis
        </h3>

        <p className="mt-2 text-sm text-slate-400">
          Mean SSIM by EuroSAT class for {method} at 25% target
          packet loss. Each class contains 50 selected images,
          evaluated across 30 seeds.
        </p>

        <div className="mt-6 space-y-4">
          {classRows.map((row) => (
            <div key={row.class_name}>
              <div className="mb-2 flex justify-between gap-4 text-sm">
                <span>{row.class_name}</span>
                <span className="font-semibold text-cyan-300">
                  {row.mean_ssim.toFixed(4)}
                </span>
              </div>

              <div className="h-3 overflow-hidden rounded-full bg-slate-800">
                <div
                  className="h-full rounded-full bg-emerald-400"
                  style={{ width: `${row.mean_ssim * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <h3 className="text-xl font-semibold">
          Interleaving Gain and Uncertainty
        </h3>

        <p className="mt-2 text-sm text-slate-400">
          Paired difference: RS Interleaved minus standard RS.
          Positive values favor interleaving. Confidence intervals
          are calculated across 30 channel seeds.
        </p>

        <div className="mt-6 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-700 text-slate-400">
              <tr>
                <th className="py-3 pr-4">RS configuration</th>
                <th className="py-3 pr-4">Packet gain</th>
                <th className="py-3 pr-4">Packet 95% CI</th>
                <th className="py-3 pr-4">SSIM gain</th>
                <th className="py-3">SSIM 95% CI</th>
              </tr>
            </thead>
            <tbody>
              {[2, 4, 8].map((parity) => {
                const packet = packetInterleaving.find(
                  (row) => row.parity === parity
                );

                const ssim = ssimInterleaving.find(
                  (row) => row.parity === parity
                );

                if (!packet || !ssim) return null;

                return (
                  <tr
                    key={parity}
                    className="border-b border-slate-800"
                  >
                    <td className="py-3 pr-4">
                      RS (8+{parity})
                    </td>
                    <td className="py-3 pr-4">
                      {packet.mean >= 0 ? "+" : ""}
                      {packet.mean.toFixed(2)} pp
                    </td>
                    <td className="py-3 pr-4">
                      [{packet.ci_lower.toFixed(2)},{" "}
                      {packet.ci_upper.toFixed(2)}] pp
                    </td>
                    <td className="py-3 pr-4">
                      {ssim.mean_ssim_gain >= 0 ? "+" : ""}
                      {ssim.mean_ssim_gain.toFixed(4)}
                    </td>
                    <td className="py-3">
                      [{ssim.ci_lower.toFixed(4)},{" "}
                      {ssim.ci_upper.toFixed(4)}]
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <p className="mt-4 text-xs text-slate-500">
          Packet gains reflect the selected target loss rate.
          SSIM gains are measured only at 25% target loss.
          Confidence intervals are nominal and not adjusted
          for multiple comparisons.
        </p>
      </div>

      <p className="text-xs text-slate-500">
        Research note: The 300,000 image-quality observations
        reuse channel recovery masks across images. They should
        not be treated as 300,000 independent channel trials.
        The 500 images are a fixed convenience sample from EuroSAT RGB.
      </p>
    </section>
  );
}
