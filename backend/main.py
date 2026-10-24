"""FastAPI backend for the Hybrid Sensor Recovery dashboard."""

from pathlib import Path
import math
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.burst_experiment import run_trial
from backend.packet_trace import packet_trace


app = FastAPI(
    title="Hybrid Sensor Recovery API",
    version="1.0.0",
    description="Interactive packet-erasure recovery simulation.",
)


LOCAL_FRONTEND_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

DEPLOYED_FRONTEND_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.getenv("FRONTEND_ORIGINS", "").split(",")
    if origin.strip()
]

ALLOWED_FRONTEND_ORIGINS = list(dict.fromkeys(
    LOCAL_FRONTEND_ORIGINS + DEPLOYED_FRONTEND_ORIGINS
))

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_FRONTEND_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class SimulationRequest(BaseModel):
    seed: int = Field(default=42, ge=0, le=1_000_000)
    loss_rate: float = Field(default=0.25, gt=0, le=0.75)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "Hybrid Sensor Recovery API",
    }


@app.post("/api/simulate")
def simulate(request: SimulationRequest):
    try:
        results = run_trial(
            seed=request.seed,
            loss_rate=request.loss_rate,
        )

        # Convert NaN values to JSON-compatible null values.
        cleaned_results = []

        for row in results:
            cleaned_results.append({
                key: (
                    None
                    if isinstance(value, float) and not math.isfinite(value)
                    else value
                )
                for key, value in row.items()
            })

        return {
            "channel": "gilbert_elliott",
            "seed": request.seed,
            "target_loss_rate": request.loss_rate,
            "methods_evaluated": len(cleaned_results),
            "results": cleaned_results,
        }

    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


class PacketTraceRequest(BaseModel):
    seed: int = Field(default=42, ge=0, le=1_000_000)
    loss_rate: float = Field(default=0.25, gt=0, le=0.75)
    parity_count: int = Field(default=4)
    interleaved: bool = Field(default=False)


@app.post("/api/packet-trace")
def get_packet_trace(request: PacketTraceRequest):
    try:
        return packet_trace(
            seed=request.seed,
            loss_rate=request.loss_rate,
            parity_count=request.parity_count,
            interleaved=request.interleaved,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


from backend.sensor_signal import sensor_signal


class SensorSignalRequest(BaseModel):
    seed: int = Field(default=42, ge=0, le=1_000_000)
    loss_rate: float = Field(default=0.25, gt=0, le=0.75)
    parity_count: int = Field(default=4)
    interleaved: bool = Field(default=True)
    signal: str = Field(default="temperature")
    start: int = Field(default=0, ge=0)
    count: int = Field(default=512, ge=1, le=2048)


@app.post("/api/sensor-signal")
def get_sensor_signal(request: SensorSignalRequest):
    try:
        return sensor_signal(
            seed=request.seed,
            loss_rate=request.loss_rate,
            parity_count=request.parity_count,
            interleaved=request.interleaved,
            signal=request.signal,
            start=request.start,
            count=request.count,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


from backend.experimental_results import experimental_results


@app.get("/api/experimental-results")
def get_experimental_results(channel: str = "burst"):
    try:
        return experimental_results(channel)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


from backend.interleaving_gain import interleaving_gain_results


@app.get("/api/interleaving-gain")
def get_interleaving_gain():
    return interleaving_gain_results()


from backend.performance_comparison import performance_comparison_results


@app.get("/api/performance-comparison")
def get_performance_comparison():
    return performance_comparison_results()


# Satellite-image simulation
from backend.satellite_simulation import satellite_simulation, METHODS


class SatelliteSimulationRequest(BaseModel):
    image_index: int = Field(default=0, ge=0)
    channel: str = Field(default="burst")
    method: str = Field(default="RS Interleaved (8+4)")
    seed: int = Field(default=42, ge=0, le=1_000_000)
    loss_rate: float = Field(default=0.25, gt=0, le=0.75)


@app.post("/api/satellite/simulate")
def simulate_satellite(request: SatelliteSimulationRequest):
    try:
        return satellite_simulation(
            image_index=request.image_index,
            channel=request.channel,
            method=request.method,
            seed=request.seed,
            loss_rate=request.loss_rate,
        )
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


# Satellite image catalog
from backend.satellite_catalog import satellite_catalog


@app.get("/api/satellite/images")
def get_satellite_images(
    class_name: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    if not 1 <= limit <= 500:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 500.",
        )

    if offset < 0:
        raise HTTPException(
            status_code=400,
            detail="offset must not be negative.",
        )

    try:
        return satellite_catalog(
            class_name=class_name,
            limit=limit,
            offset=offset,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


# Precomputed satellite research results
from backend.satellite_research import satellite_research_results


@app.get("/api/satellite/research-results")
def get_satellite_research_results(
    channel: str | None = None,
    method: str | None = None,
    loss_rate: float | None = None,
    class_name: str | None = None,
):
    try:
        return satellite_research_results(
            channel=channel,
            method=method,
            loss_rate=loss_rate,
            class_name=class_name,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
