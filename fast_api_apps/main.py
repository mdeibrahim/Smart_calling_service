from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from twilio.rest import Client
import os
from dotenv import load_dotenv
import uvicorn
from typing import List
from asgiref.sync import sync_to_async
from .stream import proxy
# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
import django
django.setup()
from apps.calling.models import Call
from apps.account.models import User

load_dotenv()

app = FastAPI()
security = HTTPBearer()

# Twilio credentials
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
twilio_phone = os.environ.get('TWILIO_PHONE_NUMBER', '+14244333353')
client = Client(account_sid, auth_token)




# Authentication functions using Django JWT
async def get_current_user(token: str):
    from rest_framework_simplejwt.tokens import AccessToken
    try:
        access_token = AccessToken(token)
        user_id = int(access_token['user_id'])
        user = await sync_to_async(User.objects.get)(id=user_id)
        return user
    except Exception as e:
        print(f"Auth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )

async def get_current_user_from_header(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return await get_current_user(credentials.credentials)

# Pydantic models
class CallRequest(BaseModel):
    customer_number: str
    seller_number: str

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
@app.websocket("/ws/{call_id}")
async def websocket_endpoint(websocket: WebSocket, call_id: int):
    await websocket.accept()
    print(f'Twilio WebSocket connected for call_id: {call_id}')
    try:
        await proxy(websocket, broadcast_to_monitors, call_id)
    except WebSocketDisconnect:
        print('Twilio WebSocket disconnected')
    except Exception as e:
        print(f'WebSocket error: {e}')
        import traceback
        traceback.print_exc()

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
async def initiate_call(call_request: CallRequest, current_user: User = Depends(get_current_user_from_header)):
    # Get ngrok URL from environment
    ngrok_url = os.environ.get('NGROK_BASE_URL', 'wss://shadeful-yun-filamentous.ngrok-free.dev')
    
    print(f"Initiating call with WebSocket URL: {ngrok_url}/ws")
    print(f"Current user: {current_user.email}, ID: {current_user.id}")
    
    try:
        # Create call record first
        print("Creating call record...")
        call_record = await sync_to_async(Call.objects.create)(
            user=current_user,
            seller_number=call_request.seller_number,
            customer_number=call_request.customer_number,
            status='initiated'
        )
        print(f"Call record created with ID: {call_record.id}")
        
        # Now make Twilio call
        print("Making Twilio call...")
        call = client.calls.create(
            twiml=f'<Response><Say>Dialing the second number now...</Say><Start><Stream url="{ngrok_url}/ws/{call_record.id}" track="both_tracks" /></Start><Dial>{call_request.customer_number}</Dial></Response>',
            to=call_request.seller_number,
            from_=twilio_phone
        )
        
        # Update with Twilio SID
        call_record.twilio_call_sid = call.sid
        await sync_to_async(call_record.save)()
        
        print(f"Call initiated successfully. Twilio SID: {call.sid}")
        
        return JSONResponse(
            content={
                "status": "success",
                "call_id": call_record.id,
                "call_sid": call.sid,
                "message": "Call initiated successfully"
            },
            status_code=200
        )
    except Exception as e:
        print(f"Error in call initiation: {e}")
        import traceback
        traceback.print_exc()
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
    print("WebSocket available at ws://localhost:5000/ws/{call_id}")
    print("Monitoring available at ws://localhost:5000/monitor")
    uvicorn.run(app, host="localhost", port=5000)