"use client";

import { useEffect, useState } from "react";
import { apiUrl } from "@/lib/api";

type SatelliteImage = {
  image_index: number;
  class_name: string;
  filename: string;
};

type SatelliteCatalog = {
  total_images: number;
  filtered_total: number;
  classes: { name: string; count: number }[];
  images: SatelliteImage[];
};

type SatelliteResult = {
  image_index: number;
  class_name: string;
  channel: string;
  method: string;
  seed: number;
  target_loss_rate: number;
  source_packets: number;
  transmitted_packets: number;
  received_packets: number;
  actual_loss_percent: number;
  exact_packets: number;
  packet_recovery_percent: number;
  redundancy_percent: number;
  psnr_db: number | null;
  ssim: number;
  exact_image_recovery: boolean;
  original_image: string;
  recovered_image: string;
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

const inputStyle =
  "w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-3 text-white";

export default function SatelliteRecovery() {
  const [catalog, setCatalog] = useState<SatelliteCatalog | null>(null);
  const [className, setClassName] = useState("");
  const [imageIndex, setImageIndex] = useState(0);
  const [channel, setChannel] = useState("burst");
  const [method, setMethod] = useState("RS Interleaved (8+4)");
  const [lossRate, setLossRate] = useState("0.25");
  const [seed, setSeed] = useState("42");
  const [result, setResult] = useState<SatelliteResult | null>(null);
  const [loadingCatalog, setLoadingCatalog] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadCatalog() {
      setLoadingCatalog(true);
      setError("");
      setResult(null);

      try {
        const params = new URLSearchParams({ limit: "50" });

        if (className) {
          params.set("class_name", className);
        }

        const response = await fetch(
          apiUrl(`/api/satellite/images?${params.toString()}`)
        );

        if (!response.ok) {
          throw new Error("Could not load satellite image catalog.");
        }

        const data: SatelliteCatalog = await response.json();

        if (!cancelled) {
          setCatalog(data);
          if (data.images.length > 0) {
            setImageIndex(data.images[0].image_index);
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Catalog loading failed."
          );
        }
      } finally {
        if (!cancelled) {
          setLoadingCatalog(false);
        }
      }
    }

    loadCatalog();

    return () => {
      cancelled = true;
    };
  }, [className]);

  async function runSimulation() {
    setRunning(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(apiUrl("/api/satellite/simulate"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          image_index: imageIndex,
          channel,
          method,
          loss_rate: Number(lossRate),
          seed: Number(seed),
        }),
      });

      if (!response.ok) {
        const body = await response.json();
        throw new Error(
          typeof body.detail === "string"
            ? body.detail
            : "Satellite simulation failed."
        );
      }

      const data: SatelliteResult = await response.json();
      setResult(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Satellite simulation failed."
      );
    } finally {
      setRunning(false);
    }
  }

  const metrics = result
    ? [
        ["Packet recovery", `${result.packet_recovery_percent.toFixed(2)}%`],
        ["SSIM", result.ssim.toFixed(4)],
        ["PSNR", result.psnr_db === null ? "∞ dB" : `${result.psnr_db.toFixed(2)} dB`],
        ["Actual packet loss", `${result.actual_loss_percent.toFixed(2)}%`],
        ["Exact source packets", `${result.exact_packets}/${result.source_packets}`],
        ["Transmitted packets", String(result.transmitted_packets)],
        ["Received transmissions", String(result.received_packets)],
        ["Redundancy", `${result.redundancy_percent.toFixed(2)}%`],
      ]
    : [];

  return (
    <section className="mt-10 space-y-6">
      <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="text-2xl font-bold">Satellite Image Recovery</h2>
        <p className="mt-2 text-sm text-slate-400">
          Reconstruct real EuroSAT RGB satellite images after simulated
          packet erasures using Reed–Solomon, interleaving, and Fountain codes.
        </p>

        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <label className="space-y-2 text-sm text-slate-300">
            <span className="block">Land-use class</span>
            <select
              className={inputStyle}
              value={className}
              disabled={loadingCatalog}
              onChange={(event) => setClassName(event.target.value)}
            >
              <option value="">All classes</option>
              {catalog?.classes.map((item) => (
                <option key={item.name} value={item.name}>
                  {item.name} ({item.count})
                </option>
              ))}
            </select>
          </label>

          <label className="space-y-2 text-sm text-slate-300">
            <span className="block">Satellite image</span>
            <select
              className={inputStyle}
              value={imageIndex}
              disabled={loadingCatalog || !catalog?.images.length}
              onChange={(event) => setImageIndex(Number(event.target.value))}
            >
              {catalog?.images.map((image) => (
                <option key={image.image_index} value={image.image_index}>
                  #{image.image_index} — {image.class_name}
                </option>
              ))}
            </select>
          </label>

          <label className="space-y-2 text-sm text-slate-300">
            <span className="block">Channel model</span>
            <select
              className={inputStyle}
              value={channel}
              onChange={(event) => setChannel(event.target.value)}
            >
              <option value="iid">IID random loss</option>
              <option value="burst">Gilbert–Elliott burst loss</option>
            </select>
          </label>

          <label className="space-y-2 text-sm text-slate-300">
            <span className="block">Recovery method</span>
            <select
              className={inputStyle}
              value={method}
              onChange={(event) => setMethod(event.target.value)}
            >
              {METHODS.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>

          <label className="space-y-2 text-sm text-slate-300">
            <span className="block">Target packet loss</span>
            <select
              className={inputStyle}
              value={lossRate}
              onChange={(event) => setLossRate(event.target.value)}
            >
              <option value="0.05">5%</option>
              <option value="0.10">10%</option>
              <option value="0.25">25%</option>
              <option value="0.50">50%</option>
              <option value="0.75">75%</option>
            </select>
          </label>

          <label className="space-y-2 text-sm text-slate-300">
            <span className="block">Random seed</span>
            <input
              className={inputStyle}
              type="number"
              min={0}
              max={1000000}
              value={seed}
              onChange={(event) => setSeed(event.target.value)}
            />
          </label>
        </div>

        <button
          type="button"
          onClick={runSimulation}
          disabled={running || loadingCatalog || !catalog?.images.length}
          className="mt-6 rounded-lg bg-cyan-500 px-6 py-3 font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:opacity-50"
        >
          {running ? "Reconstructing image..." : "Run Satellite Recovery"}
        </button>

        {loadingCatalog && (
          <p className="mt-4 text-sm text-slate-400">Loading image catalog...</p>
        )}

        {error && (
          <p role="alert" className="mt-4 text-sm text-red-400">
            {error}
          </p>
        )}
      </div>

      {result && (
        <>
          <div className="grid gap-6 md:grid-cols-2">
            {[
              { title: "Original Image", src: result.original_image },
              { title: "Recovered Image", src: result.recovered_image },
            ].map((image) => (
              <div
                key={image.title}
                className="rounded-2xl border border-slate-800 bg-slate-900 p-6"
              >
                <h3 className="mb-4 text-lg font-semibold">{image.title}</h3>
                {/* Data URLs returned by our simulation API. */}
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={image.src}
                  alt={`${image.title}: ${result.class_name}`}
                  className="aspect-square w-full rounded-lg bg-black object-contain"
                  style={{ imageRendering: "pixelated" }}
                />
              </div>
            ))}
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h3 className="text-xl font-semibold">Recovery Metrics</h3>
              <span
                className={`rounded-full px-3 py-1 text-sm ${
                  result.exact_image_recovery
                    ? "bg-emerald-500/15 text-emerald-300"
                    : "bg-amber-500/15 text-amber-300"
                }`}
              >
                {result.exact_image_recovery
                  ? "Byte-exact reconstruction"
                  : "Incomplete reconstruction"}
              </span>
            </div>

            <p className="mt-2 text-sm text-slate-400">
              {result.class_name} · {result.method} ·{" "}
              {result.channel === "burst" ? "Burst" : "IID"} ·
              Seed {result.seed}
            </p>

            <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {metrics.map(([label, value]) => (
                <div
                  key={label}
                  className="rounded-xl border border-slate-800 bg-slate-950 p-4"
                >
                  <p className="text-xs text-slate-400">{label}</p>
                  <p className="mt-2 text-xl font-semibold text-cyan-300">
                    {value}
                  </p>
                </div>
              ))}
            </div>

            <p className="mt-5 text-xs text-slate-500">
              Unrecovered packets are displayed as black pixels. SSIM and PSNR
              compare the reconstructed image with the original.
              A perfect image has infinite PSNR.
            </p>
          </div>
        </>
      )}
    </section>
  );
}
