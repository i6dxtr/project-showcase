from deepgram import Deepgram, DeepgramClient, LiveTranscriptionEvents, LiveOptions, Microphone, DeepgramClientOptions
import os
from dotenv import load_dotenv

load_dotenv("DEEPGRAM_API_KEY.env")
API_KEY = os.getenv('DEEPGRAM_API_KEY')
if not API_KEY:
    raise ValueError("API key not found!")

# Configure the DeepgramClientOptions to enable KeepAlive for maintaining the WebSocket connection (only if necessary to your scenario)
config = DeepgramClientOptions(
    options={"keepalive": "true"}
)

# Create a websocket connection using the DEEPGRAM_API_KEY from environment variables

deepgram = DeepgramClient(API_KEY)
dg_connection = deepgram.listen.websocket.v("1")

def on_open(self, open, **kwargs):
    print(f"\n\n{open}\n\n")

def on_message(self, result, **kwargs):
    sentence = result.channel.alternatives[0].transcript
    if len(sentence) == 0:
        return
    print(f"speaker: {sentence}")

def on_metadata(self, metadata, **kwargs):
    print(f"\n\n{metadata}\n\n")

def on_speech_started(self, speech_started, **kwargs):
    print(f"\n\n{speech_started}\n\n")

def on_utterance_end(self, utterance_end, **kwargs):
    print(f"\n\n{utterance_end}\n\n")

def on_error(self, error, **kwargs):
    print(f"\n\n{error}\n\n")

def on_close(self, close, **kwargs):
    print(f"\n\n{close}\n\n")

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
    ## To get UtteranceEnd, the following must be set:
    interim_results=True,
    utterance_end_ms="1000",
    vad_events=True,
)
dg_connection.start(options)

## create microphone
microphone = Microphone(dg_connection.send)

## start microphone
microphone.start()

## wait until finished
input("Press Enter to stop recording...\n\n")

## Wait for the microphone to close
microphone.finish()

## Indicate that we've finished
dg_connection.finish()

print("Finished")