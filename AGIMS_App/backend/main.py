"""
AGIMS - AI-based GNSS Integrity Monitoring System
Main FastAPI application
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
from typing import Optional
import time

from config import SIMULATION_INTERVAL, PRN_IDS, UPDATE_RATE
from schemas import (
    AttackStartRequest, StatusResponse, StartRequest,
    LiveDataMessage, AttackType
)
from data_simulator import GNSSDataSimulator
from attack_simulator import AttackSimulator
from inference import InferenceEngine
from websocket_manager import ConnectionManager

# Initialize FastAPI app
app = FastAPI(
    title="AGIMS - GNSS Integrity Monitoring System",
    description="Live GPS spoofing attack detection and visualization",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
data_simulator = GNSSDataSimulator()
attack_simulator = AttackSimulator()
inference_engine = InferenceEngine()
connection_manager = ConnectionManager()

simulation_running = False
simulation_task: Optional[asyncio.Task] = None
demo_mode = False
demo_task: Optional[asyncio.Task] = None


async def simulation_loop():
    """Main simulation loop - generates data and broadcasts updates"""
    global simulation_running
    
    print("🚀 Starting simulation loop...")
    
    while simulation_running:
        try:
            timestamp = data_simulator.get_timestamp()
            
            # Process each PRN
            for prn in PRN_IDS:
                # Generate raw data
                features = data_simulator.generate_sample(prn)
                
                # Apply attack if active
                features = attack_simulator.apply_attack(prn, features)
                
                # Run inference
                risk_score = inference_engine.process_datapoint(prn, features)
                
                # If we have a prediction, broadcast it
                if risk_score is not None:
                    attack_detected = inference_engine.is_attack_detected(risk_score)
                    
                    message = {
                        "prn": prn,
                        "timestamp": timestamp,
                        "risk_score": risk_score,
                        "attack_detected": attack_detected,
                        "raw_features": features,
                        "current_attack": attack_simulator.attack_type
                    }
                    
                    await connection_manager.broadcast(message)
            
            # Wait before next iteration
            await asyncio.sleep(SIMULATION_INTERVAL)
            
        except Exception as e:
            print(f"Error in simulation loop: {e}")
            await asyncio.sleep(0.1)
    
    print("🛑 Simulation loop stopped")


async def demo_mode_loop():
    """Demo mode - cycles through different attack types"""
    global demo_mode
    
    print("🎬 Starting demo mode...")
    
    demo_sequence = [
        ("none", 10),  # No attack for 10 seconds
        ("simplistic", 15),  # Simplistic attack for 15 seconds
        ("none", 5),  # Back to normal
        ("intermediate", 20),  # Intermediate attack
        ("none", 5),  # Back to normal
        ("sophisticated", 25),  # Sophisticated attack
        ("none", 10),  # Back to normal
    ]
    
    while demo_mode:
        for attack_type, duration in demo_sequence:
            if not demo_mode:
                break
            
            if attack_type == "none":
                attack_simulator.stop_attack()
                print(f"📊 Demo: No attack for {duration}s")
            else:
                # Apply attack to random PRNs (3-5 PRNs)
                import random
                num_prns = random.randint(3, 5)
                affected_prns = random.sample(PRN_IDS, num_prns)
                attack_simulator.start_attack(attack_type, affected_prns, intensity=1.0)
                print(f"⚠️  Demo: {attack_type} attack on PRNs {affected_prns} for {duration}s")
            
            # Wait for duration
            for _ in range(duration):
                if not demo_mode:
                    break
                await asyncio.sleep(1)
    
    # Clean up
    attack_simulator.stop_attack()
    print("🛑 Demo mode stopped")


@app.post("/start")
async def start_simulation(request: StartRequest):
    """Start the simulation"""
    global simulation_running, simulation_task, demo_mode, demo_task
    
    if simulation_running:
        raise HTTPException(status_code=400, detail="Simulation already running")
    
    # Reset everything
    data_simulator.reset()
    attack_simulator.stop_attack()
    inference_engine.reset()
    
    # Start simulation
    simulation_running = True
    simulation_task = asyncio.create_task(simulation_loop())
    
    # Start demo mode if requested
    if request.demo_mode:
        demo_mode = True
        demo_task = asyncio.create_task(demo_mode_loop())
    
    return {"status": "started", "demo_mode": request.demo_mode}


@app.post("/stop")
async def stop_simulation():
    """Stop the simulation"""
    global simulation_running, simulation_task, demo_mode, demo_task
    
    if not simulation_running:
        raise HTTPException(status_code=400, detail="Simulation not running")
    
    # Stop simulation
    simulation_running = False
    demo_mode = False
    
    # Wait for tasks to finish
    if simulation_task:
        simulation_task.cancel()
        try:
            await simulation_task
        except asyncio.CancelledError:
            pass
    
    if demo_task:
        demo_task.cancel()
        try:
            await demo_task
        except asyncio.CancelledError:
            pass
    
    # Stop any active attacks
    attack_simulator.stop_attack()
    
    return {"status": "stopped"}


@app.post("/attack/start")
async def start_attack(request: AttackStartRequest):
    """Start a spoofing attack"""
    if not simulation_running:
        raise HTTPException(status_code=400, detail="Simulation must be running")
    
    # Stop demo mode if active
    global demo_mode, demo_task
    if demo_mode:
        demo_mode = False
        if demo_task:
            demo_task.cancel()
    
    # Determine affected PRNs
    affected_prns = request.prns if request.prns else PRN_IDS
    
    # Start attack
    attack_simulator.start_attack(
        attack_type=request.attack_type.value,
        prns=affected_prns,
        intensity=request.intensity
    )
    
    return {
        "status": "attack_started",
        "attack_type": request.attack_type.value,
        "affected_prns": affected_prns,
        "intensity": request.intensity
    }


@app.post("/attack/stop")
async def stop_attack():
    """Stop the current attack"""
    attack_simulator.stop_attack()
    return {"status": "attack_stopped"}


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get current system status"""
    attack_status = attack_simulator.get_status()
    model_info = inference_engine.get_model_info()
    
    return StatusResponse(
        simulation_running=simulation_running,
        attack_active=attack_status["active"],
        attack_type=attack_status["type"] if attack_status["active"] else None,
        affected_prns=attack_status["affected_prns"],
        model_loaded=model_info["loaded"]
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "AGIMS",
        "version": "1.0.0",
        "description": "AI-based GNSS Integrity Monitoring System",
        "status": "operational",
        "endpoints": {
            "start": "POST /start",
            "stop": "POST /stop",
            "attack_start": "POST /attack/start",
            "attack_stop": "POST /attack/stop",
            "status": "GET /status",
            "websocket": "WS /ws/live"
        }
    }


@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for live data streaming"""
    await connection_manager.connect(websocket)
    
    try:
        # Send initial status
        status = await get_status()
        await connection_manager.send_personal(websocket, {
            "type": "status",
            "data": status.dict()
        })
        
        # Keep connection alive and listen for client messages
        while True:
            try:
                # Wait for messages from client (ping/pong, etc.)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_text('{"type":"ping"}')
            except WebSocketDisconnect:
                break
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await connection_manager.disconnect(websocket)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global simulation_running, demo_mode
    simulation_running = False
    demo_mode = False
    await connection_manager.close_all()


if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("  AGIMS - GNSS Integrity Monitoring System")
    print("=" * 60)
    print()
    print("  Starting server on http://localhost:8000")
    print("  WebSocket endpoint: ws://localhost:8000/ws/live")
    print("  API docs: http://localhost:8000/docs")
    print()
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)