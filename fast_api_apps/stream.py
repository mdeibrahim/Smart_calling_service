import asyncio
import base64
import difflib
import json
import time
import websockets
from pydub import AudioSegment
from groq import Groq
import os
from datetime import datetime
from apps.calling.models import Call, CallTranscript, CallReport, AIResponse
from asgiref.sync import sync_to_async

# ============================
# GLOBAL TIMING VARIABLES
# ============================
AUDIO_SENT_TIME = None
TRANSCRIPT_RECEIVED_TIME = None
LLM_START_TIME = None
FIRST_TOKEN_TIME = None
LAST_TOKEN_TIME = None
chat_history = []
current_call = None
CALL_START_TIME = None
CALL_END_TIME = None
reply_for_seller = ""

# LLM CLIENT (Groq)
groq_client = Groq(api_key=os.environ.get('GROQ_API_KEY'))

def generate_comprehensive_report(speech_list, CALL_START_TIME, CALL_END_TIME):
    total_duration = get_time(CALL_START_TIME, CALL_END_TIME)
    prompt_stats = calculate_prompt_utilization(speech_list)
    avg_response_time = calculate_average_response_time(speech_list)
    
    prompt = f"""
You are a professional sales coach analyzing a seller's call performance. Generate a comprehensive coaching report in JSON format.

**CALL DATA:**
Duration: {total_duration} (mm:ss)
Average Response Time: {avg_response_time} seconds
AI Prompt Usage: {prompt_stats['used_as_is_percentage']}%
Off-Script: {prompt_stats['off_script_percentage']}%

Transcript:
{chat_history}

Generate a comprehensive JSON analysis with performance_score and call_status fields.
"""
    
    completion = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
    )
    return completion.choices[0].message.content


def get_time(start_time, end_time):
    """Get current time in mm:ss format from conversation start"""
    elapsed = end_time - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    return f"{minutes:02d}:{seconds:02d}"

def calculate_prompt_utilization(speech_list):
    """Calculate AI prompt utilization metrics from speech list."""
    agent_speeches = [s for s in speech_list if s.get("role") == "seller" and s.get("ai_used_percentage") is not None]
    
    if not agent_speeches:
        return {
            "used_as_is_percentage": 0.0,
            "off_script_percentage": 0.0,
            "total_agent_responses": 0
        }
    
    total_ai_similarity = sum(s.get("ai_used_percentage", 0) for s in agent_speeches)
    avg_ai_usage = (total_ai_similarity / len(agent_speeches)) * 100
    off_script = 100 - avg_ai_usage
    
    return {
        "used_as_is_percentage": round(avg_ai_usage, 2),
        "off_script_percentage": round(off_script, 2),
        "total_agent_responses": len(agent_speeches)
    }

def parse_timestamp(ts):
    """Convert 'MM:SS' to seconds."""
    try:
        minutes, seconds = map(int, ts.split(":"))
        return minutes * 60 + seconds
    except:
        return 0

def calculate_average_response_time(speech_list):
    response_times = []

    for i in range(len(speech_list) - 1):
        current = speech_list[i]
        next_speech = speech_list[i + 1]

        if current["role"] == "seller" and next_speech["role"] == "customer":
            seller_time = parse_timestamp(current["timestamp"])
            customer_time = parse_timestamp(next_speech["timestamp"])
            
            diff = customer_time - seller_time
            if diff >= 0:
                response_times.append(diff)

    if response_times:
        return round(sum(response_times) / len(response_times), 2)
    return 0.0

def get_current_timestamp():
    global CALL_START_TIME
    """Get current time in mm:ss format from conversation start"""
    if not CALL_START_TIME:
        return "00:00"
    elapsed = time.time() - CALL_START_TIME
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    return f"{minutes:02d}:{seconds:02d}"


async def generate_llm_response(user_text):
    global LLM_START_TIME, FIRST_TOKEN_TIME, LAST_TOKEN_TIME

    print("\n=== LLM Suggestion Start ===")
    context = chat_history[-4:] if chat_history else []

    LLM_START_TIME = time.time()
    
    full_response = ""

    completion = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": f"You are a PitchProx. PitchProx is a system that helps the seller by suggesting responses based on customer's words. Context: {context}. Give me only one response"},
            {"role": "user", "content": user_text}
        ],
        temperature=0.8,
        max_completion_tokens=200,
        top_p=1.0,
        stream=True
    )

    loop = asyncio.get_event_loop()

    def iterate():
        nonlocal full_response
        global FIRST_TOKEN_TIME, LAST_TOKEN_TIME
        first_token_received = False

        for chunk in completion:
            delta = chunk.choices[0].delta.content
            if delta:
                if not first_token_received:
                    FIRST_TOKEN_TIME = time.time()
                    first_token_received = True
                    ttft = FIRST_TOKEN_TIME - LLM_START_TIME
                    print(f"\n[First Token Latency: {ttft:.3f}s]")
                
                print(delta, end="", flush=True)
                full_response += delta  
                LAST_TOKEN_TIME = time.time()

        if FIRST_TOKEN_TIME and LAST_TOKEN_TIME:
            if TRANSCRIPT_RECEIVED_TIME:
                end_to_end = LAST_TOKEN_TIME - TRANSCRIPT_RECEIVED_TIME
                print(f"  Transcript → LLM Complete: {end_to_end:.3f}s")

    await loop.run_in_executor(None, iterate)
    print("\n=== LLM Suggestion End ===\n")
    return full_response


def deepgram_connect():
    extra_headers = {
        'Authorization': f"Token {os.environ.get('DEEPGRAM_API_KEY', '')}"
    }
    deepgram_ws = websockets.connect(
        "wss://api.deepgram.com/v1/listen?encoding=mulaw&sample_rate=8000&channels=2&multichannel=true",
        additional_headers=extra_headers
    )
    return deepgram_ws


async def proxy(client_ws, broadcast_callback=None, call_id=None):
    global reply_for_seller, current_call, chat_history, CALL_START_TIME, CALL_END_TIME
    
    # Reset global variables for new call
    chat_history = []
    CALL_START_TIME = None
    CALL_END_TIME = None
    reply_for_seller = ""

    if call_id:
        try:
            current_call = await sync_to_async(Call.objects.get)(id=call_id)
            print(f"Loaded call record: {current_call.id}")
        except Exception as e:
            print(f"Error loading call: {e}")
            current_call = None
    else:
        current_call = None

    outbox = asyncio.Queue()
    print('started proxy')

    async with deepgram_connect() as deepgram_ws:

        async def deepgram_sender(deepgram_ws):
            global AUDIO_SENT_TIME
            print('started deepgram sender')
            while True:
                chunk = await outbox.get()
                if chunk == b'':
                    break
                AUDIO_SENT_TIME = time.time()
                await deepgram_ws.send(chunk)
            print('finished deepgram sender')

        async def deepgram_receiver(deepgram_ws):
            global TRANSCRIPT_RECEIVED_TIME, AUDIO_SENT_TIME, reply_for_seller

            print('started deepgram receiver')

            try:
                async for message in deepgram_ws:
                    try:
                        dg_json = json.loads(message)
                        
                        transcript = dg_json.get("channel", {}).get("alternatives", [{}])[0].get("transcript", "")
                        channel_index = dg_json.get("channel_index", [])

                        if transcript:
                            TRANSCRIPT_RECEIVED_TIME = time.time()
                            current_time = get_current_timestamp()
                            
                            if AUDIO_SENT_TIME:
                                deepgram_latency = TRANSCRIPT_RECEIVED_TIME - AUDIO_SENT_TIME
                            
                            if channel_index == [0, 2]:  # Seller speaking
                                print(f"\n[SELLER]: {transcript}")
                                similarity = difflib.SequenceMatcher(None, reply_for_seller, transcript).ratio()
                                chat_history.append({
                                    "role": "seller",
                                    "content": transcript,
                                    "timestamp": current_time,
                                    "ai_used_percentage": similarity
                                })
                                
                                if current_call:
                                    await sync_to_async(CallTranscript.objects.create)(
                                        call=current_call,
                                        role='caller',  # Maps to seller in DB
                                        content=transcript,
                                        timestamp=current_time,
                                        ai_used_percentage=similarity
                                    )
                                    current_call.status = 'in_progress'
                                    await sync_to_async(current_call.save)()
                                
                                if AUDIO_SENT_TIME:
                                    print(f"[Deepgram Latency: {deepgram_latency:.3f}s]")
                                
                                msg = {
                                    "type": "transcript",
                                    "role": "seller",
                                    "content": transcript,
                                    "timestamp": current_time,
                                    "ai_used_percentage": similarity
                                }
                                
                                await client_ws.send_text(json.dumps(msg))
                                
                                if broadcast_callback:
                                    await broadcast_callback(msg)
                                    
                            elif channel_index == [1, 2]:  # Customer speaking
                                print(f"\n[CUSTOMER]: {transcript}")
                                if AUDIO_SENT_TIME:
                                    print(f"[Deepgram Latency: {deepgram_latency:.3f}s]")
                                
                                reply_for_seller = await generate_llm_response(transcript)
                                chat_history.append({
                                    "role": "customer",
                                    "content": transcript,
                                    "timestamp": current_time
                                })
                                
                                if current_call:
                                    transcript_obj = await sync_to_async(CallTranscript.objects.create)(
                                        call=current_call,
                                        role='callee',  # Maps to customer in DB
                                        content=transcript,
                                        timestamp=current_time
                                    )
                                    await sync_to_async(AIResponse.objects.create)(
                                        call=current_call,
                                        transcript=transcript_obj,
                                        suggestion=reply_for_seller,
                                        timestamp=current_time
                                    )
                                
                                transcript_msg = {
                                    "type": "transcript",
                                    "role": "customer",
                                    "content": transcript,
                                    "timestamp": current_time
                                }
                                
                                suggestion_msg = {
                                    "type": "suggestion",
                                    "content": reply_for_seller,
                                    "timestamp": current_time
                                }
                                
                                await client_ws.send_text(json.dumps(transcript_msg))
                                await client_ws.send_text(json.dumps(suggestion_msg))
                                
                                if broadcast_callback:
                                    await broadcast_callback(transcript_msg)
                                    await broadcast_callback(suggestion_msg)

                    except Exception as e:
                        print(f'Error parsing deepgram response: {e}')
                        continue
                        
            except websockets.exceptions.ConnectionClosedError as e:
                print(f'Deepgram connection closed: {e}')
            except Exception as e:
                print(f'Deepgram receiver error: {e}')

            print('finished deepgram receiver')

        async def client_receiver(client_ws):
            global CALL_START_TIME, CALL_END_TIME
            print('started client receiver')

            BUFFER_SIZE = 20 * 160
            inbuffer = bytearray(b'')
            outbuffer = bytearray(b'')
            empty_byte_received = False
            inbound_chunks_started = False
            outbound_chunks_started = False
            latest_inbound_timestamp = 0
            latest_outbound_timestamp = 0

            try:
                while True:
                    message = await client_ws.receive_text()
                    
                    try:
                        data = json.loads(message)

                        if data["event"] in ("connected", "start"):
                            CALL_START_TIME = time.time()
                            if current_call:
                                current_call.started_at = datetime.fromtimestamp(CALL_START_TIME)
                                await sync_to_async(current_call.save)()
                            print("Media WS: Received event connected or start")
                            continue

                        if data["event"] == "media":
                            media = data["media"]
                            chunk = base64.b64decode(media["payload"])

                            if media['track'] == 'inbound':
                                if inbound_chunks_started:
                                    if latest_inbound_timestamp + 20 < int(media['timestamp']):
                                        bytes_to_fill = 8 * (int(media['timestamp']) - (latest_inbound_timestamp + 20))
                                        print('INBOUND WARNING! filling silence')
                                        inbuffer.extend(b"\xff" * bytes_to_fill)
                                else:
                                    print('started receiving inbound chunks!')
                                    inbound_chunks_started = True
                                    latest_inbound_timestamp = int(media['timestamp'])
                                    latest_outbound_timestamp = int(media['timestamp']) - 20

                                latest_inbound_timestamp = int(media['timestamp'])
                                inbuffer.extend(chunk)

                            if media['track'] == 'outbound':
                                outbound_chunks_started = True
                                if latest_outbound_timestamp + 20 < int(media['timestamp']):
                                    bytes_to_fill = 8 * (int(media['timestamp']) - (latest_outbound_timestamp + 20))
                                    print('OUTBOUND WARNING! filling silence')
                                    outbuffer.extend(b"\xff" * bytes_to_fill)

                                latest_outbound_timestamp = int(media['timestamp'])
                                outbuffer.extend(chunk)

                            if chunk == b'':
                                empty_byte_received = True

                        if data["event"] == "stop":
                            CALL_END_TIME = time.time()
                            print("Media WS: Received event stop")
                            print(chat_history)
                            
                            summary = generate_comprehensive_report(chat_history, CALL_START_TIME, CALL_END_TIME)
                            print("\n=== Comprehensive Call Analysis ===")
                            print(summary)
                            
                            if current_call:
                                try:
                                    # Parse JSON response
                                    summary_dict = json.loads(summary) if isinstance(summary, str) else summary
                                    
                                    # Extract fields
                                    performance_score = summary_dict.get('coaching_summary', {}).get('performance_score')
                                    call_status = summary_dict.get('conversion_indicators', {}).get('call_status', {}).get('status', 'completed')
                                    
                                    # Save report
                                    await sync_to_async(CallReport.objects.create)(
                                        call=current_call,
                                        report_data=summary_dict,  # Save as dict
                                        performance_score=performance_score,
                                        call_status=call_status
                                    )
                                    
                                    # Update call
                                    current_call.ended_at = datetime.fromtimestamp(CALL_END_TIME)
                                    current_call.duration_seconds = int(CALL_END_TIME - CALL_START_TIME)
                                    current_call.status = 'completed'
                                    await sync_to_async(current_call.save)()
                                    
                                except json.JSONDecodeError:
                                    print("Warning: Could not parse summary as JSON")
                                    await sync_to_async(CallReport.objects.create)(
                                        call=current_call,
                                        report_data={"raw_summary": summary},
                                        call_status='completed'
                                    )
                                except Exception as e:
                                    print(f"Error saving call report: {e}")
                            
                            summary_msg = {
                                "type": "call_summary",
                                "content": summary,
                                "chat_history": chat_history
                            }
                            
                            await client_ws.send_text(json.dumps(summary_msg))
                            
                            if broadcast_callback:
                                await broadcast_callback(summary_msg)
                            
                            break

                        while len(inbuffer) >= BUFFER_SIZE and len(outbuffer) >= BUFFER_SIZE or empty_byte_received:
                            if empty_byte_received:
                                break

                            asinbound = AudioSegment(inbuffer[:BUFFER_SIZE], sample_width=1, frame_rate=8000, channels=1)
                            asoutbound = AudioSegment(outbuffer[:BUFFER_SIZE], sample_width=1, frame_rate=8000, channels=1)
                            mixed = AudioSegment.from_mono_audiosegments(asinbound, asoutbound)

                            outbox.put_nowait(mixed.raw_data)
                            inbuffer = inbuffer[BUFFER_SIZE:]
                            outbuffer = outbuffer[BUFFER_SIZE:]

                    except Exception as e:
                        print(f'Error processing client message: {e}')
                        continue
                        
            except Exception as e:
                print(f'client_receiver error: {e}')

            outbox.put_nowait(b'')
            print('finished client receiver')

        await asyncio.gather(
            deepgram_sender(deepgram_ws),
            deepgram_receiver(deepgram_ws),
            client_receiver(client_ws)
        )

        try:
            await client_ws.close()
        except RuntimeError:
            pass
        print('finished running the proxy')