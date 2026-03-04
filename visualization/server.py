#!/usr/bin/env python3
"""
FastAPI server for motor vibration visualization
Receives motor status updates and broadcasts to web clients via WebSocket
"""
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import json
from datetime import datetime

app = FastAPI(title="Motor Vibration Visualizer")

# Store connected WebSocket clients
connected_clients: List[WebSocket] = []

# Current motor state
motor_state = {
    "left": False,
    "right": False,
    "intensity_left": 0.0,
    "intensity_right": 0.0,
    "target_object": None,
    "position": None,  # "left", "right", "center"
    "last_update": None
}


class MotorUpdate(BaseModel):
    """Motor status update from the perception system"""
    left: bool = False
    right: bool = False
    intensity_left: float = 1.0
    intensity_right: float = 1.0
    target_object: Optional[str] = None
    position: Optional[str] = None


class DetectionUpdate(BaseModel):
    """Detection info from the perception system"""
    target_object: str
    position: str  # "left", "right", "center"
    confidence: float = 0.0


async def broadcast_state():
    """Broadcast current motor state to all connected clients"""
    if connected_clients:
        message = json.dumps({
            "type": "motor_state",
            "data": motor_state
        })
        disconnected = []
        for client in connected_clients:
            try:
                await client.send_text(message)
            except:
                disconnected.append(client)
        
        # Remove disconnected clients
        for client in disconnected:
            connected_clients.remove(client)


@app.get("/")
async def root():
    """Serve the main visualization page"""
    return FileResponse("static/index.html")


@app.post("/api/motor/update")
async def update_motor(update: MotorUpdate):
    """
    Update motor state - called by the perception system
    
    Example:
        POST /api/motor/update
        {"left": true, "right": false, "target_object": "bottle", "position": "left"}
    """
    global motor_state
    
    motor_state["left"] = update.left
    motor_state["right"] = update.right
    motor_state["intensity_left"] = update.intensity_left
    motor_state["intensity_right"] = update.intensity_right
    motor_state["target_object"] = update.target_object
    motor_state["position"] = update.position
    motor_state["last_update"] = datetime.now().isoformat()
    
    await broadcast_state()
    
    return {"status": "ok", "state": motor_state}


@app.post("/api/motor/left/{state}")
async def set_left_motor(state: bool, intensity: float = 1.0):
    """Quick endpoint to toggle left motor"""
    motor_state["left"] = state
    motor_state["intensity_left"] = intensity if state else 0.0
    motor_state["last_update"] = datetime.now().isoformat()
    await broadcast_state()
    return {"status": "ok", "left": state}


@app.post("/api/motor/right/{state}")
async def set_right_motor(state: bool, intensity: float = 1.0):
    """Quick endpoint to toggle right motor"""
    motor_state["right"] = state
    motor_state["intensity_right"] = intensity if state else 0.0
    motor_state["last_update"] = datetime.now().isoformat()
    await broadcast_state()
    return {"status": "ok", "right": state}


@app.post("/api/motor/both/{state}")
async def set_both_motors(state: bool, intensity: float = 1.0):
    """Toggle both motors (center detection)"""
    motor_state["left"] = state
    motor_state["right"] = state
    motor_state["intensity_left"] = intensity if state else 0.0
    motor_state["intensity_right"] = intensity if state else 0.0
    motor_state["position"] = "center" if state else None
    motor_state["last_update"] = datetime.now().isoformat()
    await broadcast_state()
    return {"status": "ok", "both": state}


@app.post("/api/detection")
async def detection_update(detection: DetectionUpdate):
    """
    Receive detection update and trigger appropriate motors
    
    Example:
        POST /api/detection
        {"target_object": "bottle", "position": "left", "confidence": 0.85}
    """
    motor_state["target_object"] = detection.target_object
    motor_state["position"] = detection.position
    motor_state["last_update"] = datetime.now().isoformat()
    
    # Set motors based on position
    if detection.position == "left":
        motor_state["left"] = True
        motor_state["right"] = False
        motor_state["intensity_left"] = min(detection.confidence + 0.3, 1.0)
        motor_state["intensity_right"] = 0.0
    elif detection.position == "right":
        motor_state["left"] = False
        motor_state["right"] = True
        motor_state["intensity_left"] = 0.0
        motor_state["intensity_right"] = min(detection.confidence + 0.3, 1.0)
    elif detection.position == "center":
        motor_state["left"] = True
        motor_state["right"] = True
        intensity = min(detection.confidence + 0.3, 1.0)
        motor_state["intensity_left"] = intensity
        motor_state["intensity_right"] = intensity
    
    await broadcast_state()
    return {"status": "ok", "state": motor_state}


@app.get("/api/motor/state")
async def get_motor_state():
    """Get current motor state"""
    return motor_state


@app.post("/api/motor/stop")
async def stop_motors():
    """Stop all motors"""
    motor_state["left"] = False
    motor_state["right"] = False
    motor_state["intensity_left"] = 0.0
    motor_state["intensity_right"] = 0.0
    motor_state["target_object"] = None
    motor_state["position"] = None
    motor_state["last_update"] = datetime.now().isoformat()
    await broadcast_state()
    return {"status": "ok", "message": "All motors stopped"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time motor state updates"""
    await websocket.accept()
    connected_clients.append(websocket)
    
    # Send current state on connection
    await websocket.send_text(json.dumps({
        "type": "motor_state",
        "data": motor_state
    }))
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle ping/pong for connection keep-alive
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    
    except WebSocketDisconnect:
        if websocket in connected_clients:
            connected_clients.remove(websocket)


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("Motor Vibration Visualizer Server")
    print("=" * 60)
    print("\nOpen http://localhost:8000 in your browser")
    print("\nAPI Endpoints:")
    print("  POST /api/motor/update - Update motor state")
    print("  POST /api/motor/left/{true|false} - Toggle left motor")
    print("  POST /api/motor/right/{true|false} - Toggle right motor")
    print("  POST /api/motor/both/{true|false} - Toggle both motors")
    print("  POST /api/detection - Send detection with position")
    print("  POST /api/motor/stop - Stop all motors")
    print("  GET  /api/motor/state - Get current state")
    print("  WS   /ws - WebSocket for real-time updates")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
