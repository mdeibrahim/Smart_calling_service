from twilio.rest import Client
import time
import requests
import json
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']

client = Client(account_sid, auth_token)

call = client.calls.create(
  twiml = '<Response><Say>Dialing the second number now...</Say><Start><Stream url="wss://shadeful-yun-filamentous.ngrok-free.dev" track="both_tracks" /></Start><Dial>+8801770295204</Dial></Response>', # coller number
  to = '+8801722989557', # callee number 
  from_ = '+14244333353'
)

print(call.sid)
