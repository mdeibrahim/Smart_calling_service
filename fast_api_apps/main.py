from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from twilio.rest import Client
import os
from dotenv import load_dotenv
import asyncio
import json
import uvicorn
from typing import List

load_dotenv()

app = FastAPI()

# Twilio credentials
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']

client = Client(account_sid, auth_token)

# Import the proxy function from stream module
from stream import proxy

# Store active monitoring connections
monitoring_connections: List[WebSocket] = []

async def broadcast_to_monitors(message: dict):
    """Send message to all monitoring WebSocket connections"""
    disconnected = []
    for connection in monitoring_connections:
        try:
            await connection.send_json(message)
        except:
            disconnected.append(connection)
    
    # Remove disconnected connections
    for conn in disconnected:
        if conn in monitoring_connections:
            monitoring_connections.remove(conn)

# WebSocket endpoint for Twilio (call audio stream)
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print('Twilio WebSocket connected')
    try:
        await proxy(websocket, broadcast_to_monitors)
    except WebSocketDisconnect:
        print('Twilio WebSocket disconnected')
    except Exception as e:
        print(f'WebSocket error: {e}')

# WebSocket endpoint for monitoring (Postman/Frontend)
@app.websocket("/monitor")
async def monitor_endpoint(websocket: WebSocket):
    await websocket.accept()
    monitoring_connections.append(websocket)
    print(f'Monitor connected. Total monitors: {len(monitoring_connections)}')
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in monitoring_connections:
            monitoring_connections.remove(websocket)
        print(f'Monitor disconnected. Remaining monitors: {len(monitoring_connections)}')

# API endpoint to initiate call
@app.post("/call-initiate")
async def initiate_call():
    # Get ngrok URL from environment
    ngrok_url = os.environ.get('NGROK_BASE_URL', 'wss://shadeful-yun-filamentous.ngrok-free.dev')
    
    print(f"Initiating call with WebSocket URL: {ngrok_url}/ws")
    
    try:
        call = client.calls.create(
            twiml=f'<Response><Say>Dialing the second number now...</Say><Start><Stream url="{ngrok_url}/ws" track="both_tracks" /></Start><Dial>+8801770295204</Dial></Response>',
            to='+8801756811349',
            from_='+14244333353'
        )
        
        return JSONResponse(
            content={
                "status": "success",
                "call_sid": call.sid,
                "message": "Call initiated successfully"
            },
            status_code=200
        )
    except Exception as e:
        return JSONResponse(
            content={
                "status": "error",
                "message": str(e)
            },
            status_code=500
        )

# Health check endpoint
@app.get("/")
async def root():
    return {"status": "running", "message": "FastAPI server is running"}

if __name__ == "__main__":
    print("Starting FastAPI server on http://localhost:5000")
    print("WebSocket available at ws://localhost:5000/ws")
    print("Monitoring available at ws://localhost:5000/monitor")
    uvicorn.run(app, host="localhost", port=5000)