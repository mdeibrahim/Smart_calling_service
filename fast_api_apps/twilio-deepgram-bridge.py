
import asyncio
import base64
import difflib
import json
import sys
import time
import websockets
import ssl
from pydub import AudioSegment
from groq import Groq 
from datetime import datetime
import os

# ============================
# GLOBAL TIMING VARIABLES
# ============================
AUDIO_SENT_TIME = None           # When audio was sent to Deepgram
TRANSCRIPT_RECEIVED_TIME = None  # When transcript arrived
LLM_START_TIME = None            # When LLM request started
FIRST_TOKEN_TIME = None          # When first LLM token arrived
LAST_TOKEN_TIME = None           # When last LLM token arrived
chat_history = []      # To maintain chat history if needed
CALL_START_TIME = None  # When the call started
CALL_END_TIME = None    # When the call ended

# LLM CLIENT (Groq)

groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def generate_comprehensive_report(speech_list, CALL_START_TIME, CALL_END_TIME):
    total_duration = get_time(CALL_START_TIME, CALL_END_TIME)
    prompt_stats = calculate_prompt_utilization(speech_list)
    avg_response_time = calculate_average_response_time(speech_list)
    prompt = f"""
You are a professional sales coach analyzing an caller's call performance. Generate a comprehensive coaching report.

**CRITICAL RULES:**
- Analyze ONLY the caller's behavior, speech, and actions
- Do NOT analyze or infer the callee's emotions, intentions, or reactions
- Use phrases like "You slowed your pacing after early hesitation" (NOT "The lead seemed hesitant")
- All timestamps should reference caller actions only
- No assumptions about the other party's state

**CALL DATA:**
Duration: {total_duration} (mm:ss)
Average Response Time: {avg_response_time} seconds
AI Prompt Usage: {prompt_stats['used_as_is_percentage']}%
Off-Script: {prompt_stats['off_script_percentage']}%

Transcript:
{chat_history}

**REQUIRED OUTPUT (JSON):**
{{
  "call_summary": {{
    "agent_centric_overview": "5-8 sentence summary of agent's actions during call without transcripts",
    "call_overview": [
      "Bullet point 1: High-level behavior summary",
      "Bullet point 2: Strategy and objection navigation", 
      "Bullet point 3: Closing effort assessment"
    ]
  }},
  
  "key_moments_log": [
    {{
      "timestamp": "MM:SS",
      "action": "Agent action description",
      "significance": "Why this was important",
      "reference": "Psychological principle or statistic"
    }}
  ],
  
  "performance_metrics": {{
    "call_duration": {{
        "total_duration": "{total_duration}",
    }},
    "response_timing": {{
      "average_response_time_seconds": {avg_response_time},
      "pacing_analysis": "2-3 sentence analysis of pacing and adaptability based on the {avg_response_time}s average response time. Explain if this is optimal (1-3s is ideal), too fast (<1s), or needs improvement (>5s)."
    }},
    "prompt_utilization": {{
      "used_as_is_percentage": {prompt_stats['used_as_is_percentage']},
      "off_script_percentage": {prompt_stats['off_script_percentage']},
      "coaching_insights": "Analyze the {prompt_stats['used_as_is_percentage']}% AI usage rate. Optimal range is 40-70%. Explain if agent relied too heavily on prompts (>80%), showed good balance (40-70%), or went too off-script (<30%). Discuss natural delivery effectiveness."
    }}
  }},
  
  "conversion_indicators": {{
    "call_status": {{
      "status": "Success/In Progress/Needs Revisit",
      "reasoning": "2-4 sentence explanation based on agent behaviors and the performance score out of 100"
    }},
    "follow_up_suggestion": "Next step recommendation based on behavioral patterns"
  }},
  
  "tone_delivery_feedback": {{
    "tone_alignment": {{
      "evaluation": "2-3 sentence evaluation with timestamps",
      "key_moments": [
        {{"timestamp": "MM:SS", "tone_quality": "description"}}
      ]
    }},
    "energy_profile": {{
      "classification": "Low/Neutral/High",
      "reasoning": "2-3 sentence reasoning with timestamps and reference to {avg_response_time}s response time",
      "momentum_insights": "How pacing supported conversation",
      "reference": "Psychological principle or case study"
    }}
  }},
  
  "sentiment_responsiveness": {{
    "sentiment_signal": {{
      "score": "+1 to -1 scale",
      "explanation": "The sentiment score of is calculated from -1.0 (very negative language patterns) to +1.0 (very positive language patterns). Scores above 0.3 indicate strong positive engagement, 0.0 to 0.3 is neutral/professional, -0.3 to 0.0 shows some hesitation, and below -0.3 indicates concerning negativity. Explain what this score means for this agent's performance.",
      "timestamped_moments": [
        {{"timestamp": "MM:SS", "observation": "1-2 sentence explanation of sentiment at this moment"}}
      ]
    }},
    "adaptability_moments": [
      {{
        "timestamp": "MM:SS",
        "category": "tone/pacing/strategy",
        "description": "1-2 sentence reasoning",
        "reference": "Psychological principle"
      }}
    ],
    "coaching_tags": [
      {{
        "tag": "reassuring/assertive/empathetic/hesitant",
        "timestamp": "MM:SS",
        "reasoning": "1-3 sentence explanation"
      }}
    ]
  }},
  
  "behavioral_coaching": {{
    "supportive_language_use": [
      {{
        "timestamp": "MM:SS",
        "example": "Specific phrasing used",
        "analysis": "How it supports potential hesitation/clarity needs"
      }}
    ],
    "conversational_flexibility": "2-3 sentence evaluation of adaptation. Reference the {prompt_stats['off_script_percentage']}% off-script rate.",
    "trust_oriented_behaviors": [
      {{
        "behavior": "Description",
        "example": "Specific instance with timestamp",
        "reasoning": "2-3 sentences",
        "reference": "Psychological principle",
        "reference_url": "URL if applicable"
      }}
    ]
  }},
  
  "coaching_summary": {{
    "performance_score": out of 100,
    "score_breakdown": "Explain the score. It's calculated from: AI prompt usage (30%), response timing (20%), call engagement (25%), and call duration appropriateness (25%). Scores 80+ are excellent, 60-79 good, 40-59 needs improvement, below 40 requires coaching.",
    "improvement_areas": [
      {{
        "area": "Specific guidance area",
        "description": "2-3 sentence explanation",
        "timestamped_example": "MM:SS - specific suggestion"
      }}
    ],
    "ai_coaching_highlights": [
      "Positive/constructive note 1 with reasoning",
      "Positive/constructive note 2 with reasoning",
      "Positive/constructive note 3 with reasoning"
    ]
  }},
  
  "defining_moments": {{
    "prompt_usage": [
      {{
        "timestamp": "MM:SS",
        "description": "1-2 sentences on how/why/when agent used or deviated from AI prompts",
        "effectiveness": "evaluation"
      }}
    ],
    "objection_navigation": [
      {{
        "timestamp": "MM:SS",
        "description": "1-2 sentences on how/why/when",
        "effectiveness": "evaluation"
      }}
    ],
    "rapport_building": [
      {{
        "timestamp": "MM:SS",
        "description": "1-2 sentences on how/why/when",
        "effectiveness": "evaluation"
      }}
    ],
    "ctas": [
      {{
        "timestamp": "MM:SS",
        "type": "issued/missed",
        "description": "1-2 sentences on how/why/when",
        "effectiveness": "evaluation"
      }}
    ]
  }}
}}

Generate the complete analysis now:
"""
    completion = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "user", "content": prompt}
        ],
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
    """
    Calculate AI prompt utilization metrics from speech list.
    
    Returns:
        dict with used_as_is_percentage, off_script_percentage
    """
    agent_speeches = [s for s in speech_list if s.get("role") == "caller" and s.get("ai_used_percentage") is not None]
    
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
    minutes, seconds = map(int, ts.split(":"))
    return minutes * 60 + seconds


def calculate_average_response_time(speech_list):
    response_times = []

    for i in range(len(speech_list) - 1):
        current = speech_list[i]
        next_speech = speech_list[i + 1]

        # Caller speaks → Callee responds
        if current["role"] == "caller" and next_speech["role"] == "callee":
            caller_time = parse_timestamp(current["timestamp"])
            callee_time = parse_timestamp(next_speech["timestamp"])
            
            diff = callee_time - caller_time
            if diff >= 0:
                response_times.append(diff)

    if response_times:
        return round(sum(response_times) / len(response_times), 2)
    return 0.0

# ============================================================
# Get Current Timestamp
# ============================================================
def get_current_timestamp():
    global CALL_START_TIME
    """Get current time in mm:ss format from conversation start"""
    elapsed = time.time() - CALL_START_TIME
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    return f"{minutes:02d}:{seconds:02d}"


# ============================================================
# LLM RESPONSE WITH LATENCY MEASUREMENT
# ============================================================
async def generate_llm_response(user_text):
    global LLM_START_TIME, FIRST_TOKEN_TIME, LAST_TOKEN_TIME

    print("\n=== LLM Suggestion Start ===")
    context = chat_history[-4:] if chat_history else [] # call http get methdo to get the last 4 messages


    LLM_START_TIME = time.time()
    
    full_response = ""

    completion = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": f"You are a PitchProx. PitchProx is a system that helps the caller by suggesting responses based on callee's words. Context: {context}. Give me only one response"},
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
            # total_llm_time = LAST_TOKEN_TIME - LLM_START_TIME
            # streaming_time = LAST_TOKEN_TIME - FIRST_TOKEN_TIME
            # print(f"\n\n[LLM Metrics]")
            # print(f"  Time to First Token: {FIRST_TOKEN_TIME - LLM_START_TIME:.3f}s")
            # print(f"  Total Generation Time: {total_llm_time:.3f}s")
            # print(f"  Streaming Duration: {streaming_time:.3f}s")
            
            if TRANSCRIPT_RECEIVED_TIME:
                end_to_end = LAST_TOKEN_TIME - TRANSCRIPT_RECEIVED_TIME
                print(f"  Transcript → LLM Complete: {end_to_end:.3f}s")

    await loop.run_in_executor(None, iterate)
    print("=== LLM Suggestion End ===\n")
    return full_response




# ============================
# DEEPGRAM CONNECT
# ============================
def deepgram_connect():
    deepgram_api_key = os.environ.get("DEEPGRAM_API_KEY", "")
    extra_headers = {
        'Authorization': f"Token {deepgram_api_key}"
    }
    deepgram_ws = websockets.connect(
    "wss://api.deepgram.com/v1/listen?"
    "model=nova-2&"     
    "encoding=mulaw&"
    "sample_rate=8000&"
    "channels=2&"
    "multichannel=true&"
    "punctuate=true&"         
    "smart_format=true&"     
    "language=en&"          
    "filler_words=true&"      
    "numerals=true",         
    additional_headers=extra_headers
)
    return deepgram_ws


# ============================
# MAIN PROXY
# ============================
async def proxy(client_ws, path=None):
    global DEEPGRAM_LATENCY, LLM_TRIGGER_TIME

    outbox = asyncio.Queue()
    print('started proxy')

    async with deepgram_connect() as deepgram_ws:

        async def deepgram_sender(deepgram_ws):
            print('started deepgram sender')
            while True:
                chunk = await outbox.get()
                await deepgram_ws.send(chunk)
            print('finished deepgram sender')

        async def deepgram_sender(deepgram_ws):
            global AUDIO_SENT_TIME
            print('started deepgram sender')
            while True:
                chunk = await outbox.get()
                AUDIO_SENT_TIME = time.time()  # Mark when audio is sent
                await deepgram_ws.send(chunk)
            print('finished deepgram sender')

        async def deepgram_receiver(deepgram_ws):
            global TRANSCRIPT_RECEIVED_TIME, AUDIO_SENT_TIME, reply_for_caller

            print('started deepgram receiver')

            async for message in deepgram_ws:
                try:
                    dg_json = json.loads(message)
                    
                    transcript = dg_json.get("channel", {}).get("alternatives", [{}])[0].get("transcript", "")
                    channel_index = dg_json.get("channel_index", [])

                    if transcript:
                        TRANSCRIPT_RECEIVED_TIME = time.time()
                        current_time = get_current_timestamp()
                        
                        # Calculate Deepgram latency (audio sent to transcript received)
                        if AUDIO_SENT_TIME:
                            deepgram_latency = TRANSCRIPT_RECEIVED_TIME - AUDIO_SENT_TIME
                        
                        if channel_index == [0, 2]:
                            print(f"\n[CALLER]: {transcript}")
                            similarity = difflib.SequenceMatcher(None, reply_for_caller, transcript).ratio()
                            chat_history.append({"role": "caller", "content": transcript, "timestamp": current_time, "ai_used_percentage":similarity})
                            if AUDIO_SENT_TIME:
                                print(f"[Deepgram Latency: {deepgram_latency:.3f}s]")
                                
                        elif channel_index == [1, 2]:
                            print(f"\n[CALLEE]: {transcript}")
                            if AUDIO_SENT_TIME:
                                print(f"[Deepgram Latency: {deepgram_latency:.3f}s]")
                            
                            reply_for_caller = await generate_llm_response(transcript)
                            # we get llm response here and need to send to to the screen and save to the db
                            chat_history.append({"role": "callee", "content": transcript, "timestamp": current_time}) # post save to database chat history 
                            # asyncio.create_task(generate_llm_response(transcript))

                except:
                    print('was not able to parse deepgram response as json')
                    continue

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

            async for message in client_ws:
                try:
                    data = json.loads(message)

                    if data["event"] in ("connected", "start"):
                        CALL_START_TIME = time.time()
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
                        # post save to database call summary
                        print(summary)
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

                except:
                    print('message from client not formatted correctly, bailing')
                    break

            outbox.put_nowait(b'')
            print('finished client receiver')

        await asyncio.wait([
            asyncio.ensure_future(deepgram_sender(deepgram_ws)),
            asyncio.ensure_future(deepgram_receiver(deepgram_ws)),
            asyncio.ensure_future(client_receiver(client_ws))
        ])

        client_ws.close()
        print('finished running the proxy')


async def main():
    async with websockets.serve(proxy, 'localhost', 5000):
        print('WebSocket server started on localhost:5000')
        await asyncio.Future()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\nServer stopped')
        sys.exit(0)
