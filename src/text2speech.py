import os
import pvporcupine
import pydub
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech as cloud_speech_types
import pyaudio
import dotenv
import wave
import struct
from pvrecorder import PvRecorder
from datetime import datetime
import argparse
import pvleopard as leopard
import pvleopard as pvl
from pathlib import Path
print (pvl.default_library_path)
# path to a file one directory above this file
BASE_DIR = Path(__file__).resolve().parent  # folder containing this file
TARGET = BASE_DIR.parent / ".env"  # adjust name as needed

dotenv.load_dotenv(TARGET)  # load the .env file

pydub.AudioSegment.converter = "ffmpeg"
pydub.AudioSegment.ffmpeg = "C:\\Users\\ASUS\\Desktop\\JARVIS-AI\\ffmpeg\\bin\\ffmpeg.exe"
pydub.AudioSegment.ffprobe = "C:\\Users\\ASUS\\Desktop\\JARVIS-AI\\ffmpeg\\bin\\ffprobe.exe"

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
PORCUPINE_ACCESS_KEY = os.getenv("PORCUPINE_ACCESS_KEY")

def transcribe_audio_from_mic():
    """Transcribe audio from microphone after detecting 'Hey Jarvis'."""
    
    # Initialize wake word detector
    porcupine = pvporcupine.create(
        access_key=PORCUPINE_ACCESS_KEY,
        keywords=["jarvis"],
    )

    
    print("Listening for 'Hey Jarvis'...")
    print('Porcupine version: %s' % porcupine.version)

    recorder = PvRecorder(
        frame_length=porcupine.frame_length,
        device_index=-1,)

    recorder.start()

    wav_file = None
    print('Listening ... (press Ctrl+C to exit)')

    try:
        while True:
            pcm = recorder.read()
            result = porcupine.process(pcm)

            if wav_file is not None:
                wav_file.writeframes(struct.pack("h" * len(pcm), *pcm))

            if result >= 0:
                print('Detected wake word at %s' % str(datetime.now()))
                transcribe_speech()
    except KeyboardInterrupt:
        print('Stopping ...')
    finally:
        recorder.delete()
        porcupine.delete()
        if wav_file is not None:
            wav_file.close()

def get_audio_data():
    """Capture audio data from microphone while detecting voice activity."""
    import array
    
    recorder = PvRecorder(device_index=-1)
    
    print("Recording audio... Speak now!")
    recorder.start()
    
    audio_frames = []
    silence_threshold = 500  # Adjust based on your microphone sensitivity
    silence_duration = 5.0  # Stop after 1 second of silence
    silence_frames = 0
    max_silence_frames = int(silence_duration * recorder.sample_rate / recorder.frame_length)
    
    try:
        while True:
            pcm = recorder.read()
            audio_frames.extend(pcm)
            
            # Calculate RMS (volume level) of current frame
            if len(pcm) > 0:
                rms = int((sum(sample ** 2 for sample in pcm) / len(pcm)) ** 0.5)
            else:
                rms = 0
            
            # Track silence
            if rms < silence_threshold:
                silence_frames += 1
            else:
                silence_frames = 0  # Reset if sound detected
            
            # Stop if enough silence detected
            if silence_frames > max_silence_frames:
                print("Silence detected. Stopping recording...")
                break
        
        return bytes(struct.pack("h" * len(audio_frames), *audio_frames))
    finally:
        recorder.stop()
        recorder.delete()


def transcribe_speech():
    """Transcribe speech using Leopard speech recognition model."""
    leopard = pvl.create(access_key=PORCUPINE_ACCESS_KEY, model_path="C:\\Users\\ASUS\\Desktop\\JARVIS-AI\\jarvis-leopard-default-v3.0.0-25-12-22--20-12-48.pv", enable_automatic_punctuation=True, device="CPU")
    
    try:
        # Capture audio while user speaks
        
        audio_data = get_audio_data()
        
        # Process with Leopard model
        transcript, words = leopard.process(audio_data)
        
        print(f"\n✓ Transcription: {transcript}\n")
        
        # Print word-level details
        if words:
            print("Word details:")
            for word in words:
                print(
                    f"  {{word=\"{word.word}\" start_sec={word.start_sec:.2f} end_sec={word.end_sec:.2f} confidence={word.confidence:.2f}}}"
                )
        else:
            print("No words detected.")
        
        return transcript
    finally:
        leopard.delete()

if __name__ == "__main__":
    """Start the JARVIS wake word detector and transcription system."""
    print("=" * 60)
    print("JARVIS AI Assistant - Speech Recognition System")
    print("=" * 60)
    print("\nInitializing wake word detection...")
    print("Say 'Hey Jarvis' to activate\n")
    
    try:
        transcribe_audio_from_mic()
    except KeyboardInterrupt:
        print("\n\nShutting down JARVIS...")