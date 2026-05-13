"""
AGIMS v2.0 — AI-based GNSS Integrity Monitoring System
Main FastAPI application.

Full pipeline per tick:
  source_manager → attack_simulator → inference → threat_model → decision_engine → websocket
"""
import asyncio
import logging
import random
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from config import SIMULATION_INTERVAL, PRN_IDS
from schemas import AttackStartRequest, StatusResponse, StartRequest
from simulation.data_simulator     import GNSSDataSimulator
from simulation.attack_simulator   import AttackSimulator
from detection.inference           import InferenceEngine
from intelligence.threat_model     import ThreatModel
from intelligence.decision_engine  import DecisionEngine
from data_source.source_manager    import DataSourceManager
from ws.websocket_manager   import ConnectionManager

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(title="AGIMS", description="AI-based GNSS Integrity Monitoring System", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

# ── Singletons ─────────────────────────────────────────────────────────────────
data_sim    = GNSSDataSimulator()
atk_sim     = AttackSimulator()
inference   = InferenceEngine()
threat_mdl  = ThreatModel()
decision_eg = DecisionEngine()
ws_mgr      = ConnectionManager()
src_mgr     = DataSourceManager(simulator=data_sim)

sim_running  = False
sim_task:    Optional[asyncio.Task] = None
demo_mode    = False
demo_task:   Optional[asyncio.Task] = None


# ── Simulation loop ────────────────────────────────────────────────────────────
async def simulation_loop():
    global sim_running
    logger.info("Simulation started | source=%s | PRNs=%s", src_mgr.mode, PRN_IDS)
    while sim_running:
        try:
            ts = data_sim.get_timestamp()
            for prn in PRN_IDS:
                features = src_mgr.get_data(prn)
                features = atk_sim.apply_attack(prn, features)
                risk     = inference.process_datapoint(prn, features)
                if risk is None:
                    continue
                detected = inference.is_attack_detected(risk)
                threat   = threat_mdl.assess(risk, detected)
                decision = decision_eg.decide(threat)
                await ws_mgr.broadcast({
                    "prn":             prn,
                    "timestamp":       round(ts, 3),
                    "risk_score":      round(risk, 4),
                    "attack_detected": detected,
                    "raw_features":    {k: round(v, 4) for k, v in features.items()},
                    "current_attack":  atk_sim.attack_type,
                    "data_source":     src_mgr.mode,
                    "threat":          threat,
                    "decision":        decision,
                })
            await asyncio.sleep(SIMULATION_INTERVAL)
        except Exception as e:
            logger.error("Simulation error: %s", e)
            await asyncio.sleep(0.1)
    logger.info("Simulation stopped")


async def demo_loop():
    global demo_mode
    logger.info("Demo mode started")
    sequence = [
        ("none", 10), ("simplistic", 15), ("none", 5),
        ("intermediate", 20), ("none", 5), ("sophisticated", 25), ("none", 10),
    ]
    while demo_mode:
        for atk_type, dur in sequence:
            if not demo_mode:
                break
            if atk_type == "none":
                atk_sim.stop_attack()
            else:
                n    = min(6, len(PRN_IDS))
                prns = random.sample(PRN_IDS, random.randint(3, n))
                atk_sim.start_attack(atk_type, prns, intensity=1.0)
                logger.info("Demo: %s on PRNs %s for %ds", atk_type, prns, dur)
            for _ in range(dur):
                if not demo_mode:
                    break
                await asyncio.sleep(1)
    atk_sim.stop_attack()
    logger.info("Demo mode stopped")


# ── Endpoints ──────────────────────────────────────────────────────────────────
@app.post("/start")
async def start_simulation(request: StartRequest):
    global sim_running, sim_task, demo_mode, demo_task
    if sim_running:
        raise HTTPException(400, "Simulation already running")
    data_sim.reset()
    atk_sim.stop_attack()
    inference.reset()
    sim_running = True
    sim_task    = asyncio.create_task(simulation_loop())
    if request.demo_mode:
        demo_mode = True
        demo_task = asyncio.create_task(demo_loop())
    return {"status": "started", "demo_mode": request.demo_mode,
            "data_source": src_mgr.mode, "prn_ids": PRN_IDS}


@app.post("/stop")
async def stop_simulation():
    global sim_running, sim_task, demo_mode, demo_task
    if not sim_running:
        raise HTTPException(400, "Simulation not running")
    sim_running = False
    demo_mode   = False
    for t in (sim_task, demo_task):
        if t:
            t.cancel()
            try: await t
            except asyncio.CancelledError: pass
    atk_sim.stop_attack()
    return {"status": "stopped"}


@app.post("/attack/start")
async def start_attack(request: AttackStartRequest):
    global demo_mode, demo_task
    if not sim_running:
        raise HTTPException(400, "Start simulation first")
    if demo_mode:
        demo_mode = False
        if demo_task: demo_task.cancel()
    prns = [p for p in (request.prns or PRN_IDS) if p in PRN_IDS]
    if not prns:
        raise HTTPException(400, f"No valid PRNs. Available: {PRN_IDS}")
    atk_sim.start_attack(request.attack_type.value, prns, request.intensity)
    return {"status": "attack_started", "attack_type": request.attack_type.value,
            "affected_prns": prns, "intensity": request.intensity}


@app.post("/attack/stop")
async def stop_attack():
    atk_sim.stop_attack()
    return {"status": "attack_stopped"}


@app.get("/status", response_model=StatusResponse)
async def get_status():
    atk   = atk_sim.get_status()
    model = inference.get_model_info()
    return StatusResponse(
        simulation_running=sim_running,
        attack_active=atk["active"],
        attack_type=atk["type"] if atk["active"] else None,
        affected_prns=atk["affected_prns"],
        model_loaded=model["loaded"],
        model_type=model["type"],
        data_source=src_mgr.mode,
        prn_ids=PRN_IDS,
    )


@app.get("/prns")
async def get_prns():
    return {"prn_ids": PRN_IDS, "count": len(PRN_IDS)}


@app.get("/")
async def root():
    return {"name": "AGIMS", "version": "2.0.0",
            "data_source": src_mgr.mode, "prn_ids": PRN_IDS}


@app.websocket("/ws/live")
async def ws_endpoint(ws: WebSocket):
    await ws_mgr.connect(ws)
    try:
        status = await get_status()
        await ws_mgr.send_personal(ws, {"type": "init", "data": status.dict()})
        while True:
            try:
                await asyncio.wait_for(ws.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                await ws.send_text('{"type":"ping"}')
            except WebSocketDisconnect:
                break
    except Exception as e:
        logger.error("WS error: %s", e)
    finally:
        await ws_mgr.disconnect(ws)


@app.on_event("shutdown")
async def on_shutdown():
    global sim_running, demo_mode
    sim_running = False
    demo_mode   = False
    src_mgr.close()
    await ws_mgr.close_all()


if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("  AGIMS v2.0 – GNSS Integrity Monitoring System")
    print(f"  Data source : {src_mgr.mode}")
    print(f"  PRNs ({len(PRN_IDS)})   : {PRN_IDS}")
    print("  API docs    : http://localhost:8000/docs")
    print("  WebSocket   : ws://localhost:8000/ws/live")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)
