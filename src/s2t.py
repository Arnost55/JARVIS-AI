import signal
import sys
import time
from argparse import ArgumentParser
from threading import Thread
import os
from pvleopard import available_devices, create, LeopardActivationLimitError
from pvrecorder import PvRecorder
from tabulate import tabulate
import dotenv
from pathlib import Path
import json
import numpy as np
BASE_DIR = Path(__file__).resolve().parent
TARGET = BASE_DIR.parent / ".env"
dotenv.load_dotenv(TARGET)
porcupine_access_key = os.getenv("PORCUPINE_ACCESS_KEY")
model_path = os.getenv("LEOPARD_MODEL_PATH")


class Recorder(Thread):
    def __init__(self, audio_device_index, silence_threshold=3, silence_level=500):
        super().__init__()
        self._pcm = list()
        self._is_recording = False
        self._stop = False
        self._audio_device_index = audio_device_index
        self.silence_threshold = silence_threshold  # seconds
        self.silence_level = silence_level  # Audio amplitude threshold
        self.last_audio_time = None

    def is_recording(self):
        return self._is_recording

    def run(self):
        self._is_recording = True
        recorder = PvRecorder(frame_length=160, device_index=self._audio_device_index)
        recorder.start()
        
        self.last_audio_time = time.time()  # Initialize when recording actually starts
        print("Recording started... Speak now!")

        while not self._stop:
            audio_data = recorder.read()
            self._pcm.extend(audio_data)

            # Calculate RMS (root mean square) of audio data for better silence detection
            audio_array = np.array(audio_data, dtype=np.int16)
            rms = np.sqrt(np.mean(audio_array**2))

            # Check if audio data is silent
            if rms < self.silence_level:
                if time.time() - self.last_audio_time > self.silence_threshold:
                    print(f"\nSilence detected for {self.silence_threshold}s. Stopping recording...")
                    break
            else:
                self.last_audio_time = time.time()  # Reset timer on audio detection

        recorder.stop()
        self._is_recording = False
        print("Recording stopped.")

    def stop(self):
        self._stop = True
        while self._is_recording:
            pass
        return self._pcm


def main():
    parser = ArgumentParser()
    parser.add_argument(
        '--library_path',
        help='Absolute path to dynamic library. Default: using the library provided by `pvleopard`')
    parser.add_argument(
        '--model_path',
        help='Absolute path to Leopard model. Default: using the model provided by `pvleopard`')
    parser.add_argument(
        '--device',
        help='Device to run inference on (`best`, `cpu:{num_threads}` or `gpu:{gpu_index}`).'
             'Default: automatically selects best device for `pvleopard`')
    parser.add_argument(
        '--disable_automatic_punctuation',
        action='store_true',
        help='Disable insertion of automatic punctuation')
    parser.add_argument(
        '--disable_speaker_diarization',
        action='store_true',
        help='Disable identification of unique speakers')
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print verbose output of the transcription')
    parser.add_argument(
        '--show_audio_devices',
        action='store_true',
        help='Only list available devices and exit')
    parser.add_argument(
        '--audio_device_index',
        default=-1,
        type=int,
        help='Audio device index to use from --show_audio_devices')
    parser.add_argument(
        '--show_inference_devices',
        action='store_true',
        help='Show the list of available devices for Leopard inference and exit')
    parser.add_argument(
        '--silence_threshold',
        default=1.5,
        type=float,
        help='Silence duration in seconds before stopping (default: 1.5)')
    args = parser.parse_args()

    if args.show_audio_devices:
        for index, name in enumerate(PvRecorder.get_available_devices()):
            print('Device #%d: %s' % (index, name))
        return

    if args.show_inference_devices:
        print('\n'.join(available_devices(library_path=args.library_path)))
        return

    if args.audio_device_index != -1:
        devices_length = len(PvRecorder.get_available_devices())
        if args.audio_device_index < 0 or args.audio_device_index >= devices_length:
            print('Invalid audio device index provided.')
            sys.exit(1)

    leopard = create(
        access_key=porcupine_access_key,
        model_path=model_path,
        device=args.device,
        library_path=args.library_path,
        enable_automatic_punctuation=not args.disable_automatic_punctuation,
        enable_diarization=not args.disable_speaker_diarization)

    recorder = Recorder(args.audio_device_index, silence_threshold=args.silence_threshold)
    recorder.start()

    def on_exit(_, __):
        if recorder is not None and recorder.is_recording():
            pcm_data = recorder.stop()
            if pcm_data:
                print("\nProcessing transcription...")
                transcript, words = leopard.process(pcm_data)
                print(f"\nTranscript: {transcript}")
                transcript_data = {"Transcript": transcript}
                with open("transcript.json", "w") as f:
                    json.dump(transcript_data, f, indent=4)
                print("Transcript saved to transcript.json")
                print(transcript)
        
        leopard.delete()
        print()
        sys.exit(0)

    signal.signal(signal.SIGINT, on_exit)

    print('>>> Listening... (Press CTRL+C to force exit)')

    # Keep the main thread alive while the recorder is running
    while recorder.is_recording():
        time.sleep(0.1)

    # Once recording stops automatically, process the transcription
    pcm_data = recorder.stop()
    if pcm_data:
        print("\nProcessing transcription...")
        transcript, words = leopard.process(pcm_data)
        print(f"\nTranscript: {transcript}")
        transcript_data = {"Transcript": transcript,}
        output_file = BASE_DIR / "transcript.json"
        with open(output_file, "w") as f:
            json.dump(transcript_data, f, indent=4)
        print(f"Transcript saved to {output_file}")
        print(transcript)
    
    leopard.delete()




