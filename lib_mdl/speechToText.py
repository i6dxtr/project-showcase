from deepgram import Deepgram, DeepgramClient, LiveTranscriptionEvents, LiveOptions, Microphone, DeepgramClientOptions
import os, json
from dotenv import load_dotenv

load_dotenv("DEEPGRAM_API_KEY.env")
API_KEY = os.getenv('DEEPGRAM_API_KEY')
if not API_KEY:
    raise ValueError("API key not found!")

# Configure the DeepgramClientOptions to enable KeepAlive for maintaining the WebSocket connection (only if necessary)
config = DeepgramClientOptions(options={"keepalive": "true"})

# Create a websocket connection
deepgram = DeepgramClient(API_KEY)
dg_connection = deepgram.listen.websocket.v("1")

# Store received data
received_data = {
    "open": None,
    "messages": [],
    "metadata": None,
    "speech_started": None,
    "utterance_end": None,
    "error": None,
    "close": None
}

# Updated callback functions to store data
def on_open(self, open, **kwargs):
    received_data["open"] = open
    print(f"\n\n{open}\n\n")

def on_message(self, result, **kwargs):
    sentence = result.channel.alternatives[0].transcript
    if len(sentence) == 0:
        return
    received_data["messages"].append(sentence)
    print(f"speaker: {sentence}")

def on_metadata(self, metadata, **kwargs):
    received_data["metadata"] = metadata
    print(f"\n\n{metadata}\n\n")

def on_speech_started(self, speech_started, **kwargs):
    received_data["speech_started"] = speech_started
    print(f"\n\n{speech_started}\n\n")

def on_utterance_end(self, utterance_end, **kwargs):
    received_data["utterance_end"] = utterance_end
    print(f"\n\n{utterance_end}\n\n")

def on_error(self, error, **kwargs):
    received_data["error"] = error
    print(f"\n\n{error}\n\n")

def on_close(self, close, **kwargs):
    received_data["close"] = close
    print(f"\n\n{close}\n\n")

# Register callbacks
dg_connection.on(LiveTranscriptionEvents.Open, on_open)
dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
dg_connection.on(LiveTranscriptionEvents.Metadata, on_metadata)
dg_connection.on(LiveTranscriptionEvents.SpeechStarted, on_speech_started)
dg_connection.on(LiveTranscriptionEvents.UtteranceEnd, on_utterance_end)
dg_connection.on(LiveTranscriptionEvents.Error, on_error)
dg_connection.on(LiveTranscriptionEvents.Close, on_close)

options: LiveOptions = LiveOptions(
    model="nova-3",
    punctuate=True,
    language="en-US",
    encoding="linear16",
    channels=1,
    sample_rate=16000,
    interim_results=True, # Required for UtteranceEnd
    utterance_end_ms="1000",
    vad_events=True,
)

dg_connection.start(options)

# Create and start the microphone
microphone = Microphone(dg_connection.send)
microphone.start()

# Wait until finished
input("Press Enter to stop recording...\n\n")

# Wait for the microphone to close
microphone.finish()

# Indicate that we've finished
dg_connection.finish()

# Display collected data
print("\nCollected Data:")
print(received_data)

print("Finished")

print("\nCollected Data (Formatted):")
print(json.dumps(received_data, indent=4))