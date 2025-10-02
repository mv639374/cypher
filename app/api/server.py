import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import socketio
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import our compiled graph from main.py
from app.main import graph

# --- FastAPI and CORS Setup ---
fast_api_app = FastAPI()
fast_api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# --- Socket.IO Server Setup ---
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
socket_app = socketio.ASGIApp(sio, other_asgi_app=fast_api_app)

# --- Helper Function for Serialization ---
def convert_pydantic_to_dict(obj):
    """
    Recursively converts Pydantic models in an object to dictionaries.
    """
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    if isinstance(obj, dict):
        return {k: convert_pydantic_to_dict(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_pydantic_to_dict(i) for i in obj]
    return obj

# --- Background Task for Graph Execution ---
async def run_graph_streaming(sid, initial_state: dict):
    """
    Runs the LangGraph stream in the background and emits events to the client.
    """
    try:
        for event in graph.stream(initial_state, {"recursion_limit": 25}):
            # Convert the event to be JSON serializable BEFORE emitting
            serializable_event = convert_pydantic_to_dict(event)
            await sio.emit('graph_event', data=serializable_event, to=sid)
            await asyncio.sleep(0.1)
        
        await sio.emit('graph_finished', to=sid)

    except Exception as e:
        print(f"Error during graph execution: {e}")
        await sio.emit('graph_error', data={'error': str(e)}, to=sid)

# --- WebSocket Event Handlers ---
@sio.event
async def connect(sid, environ):
    print(f"Socket.IO client connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"Socket.IO client disconnected: {sid}")

@sio.event
async def investigate(sid, data: dict):
    """
    This event is triggered by the frontend to start an investigation.
    """
    print(f"Received investigation request from {sid}: {data}")
    
    initial_state = {
        "alert": {"source": "manual", "details": data.get("prompt")},
        "indicator": data.get("indicator", ""),
        "logs": data.get("logs", ""),
    }
    
    sio.start_background_task(run_graph_streaming, sid, initial_state)
    await sio.emit('investigation_started', to=sid)