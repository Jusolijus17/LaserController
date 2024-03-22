from tkinter import OFF
import pyaudio
import numpy as np
import broadlink
import queue
import time

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
VOLUME_THRESHOLD_FACTOR = 1.5
AVERAGE_WINDOW = 50
KICK_DETECTION_INTERVAL = 0.5  # Secondes
MINIMUM_VOLUME_THRESHOLD = 500000   # Ajustez cette valeur en fonction de vos besoins

volume_queue = queue.Queue(maxsize=AVERAGE_WINDOW)
average_volume = 0
last_kick_time = 0

def update_volume_average(new_volume):
    global average_volume
    if volume_queue.full():
        volume_queue.get()
    volume_queue.put(new_volume)
    average_volume = sum(volume_queue.queue) / volume_queue.qsize()

def is_kick_detected(current_volume, average_volume, current_time):
    global last_kick_time
    if current_volume > average_volume * VOLUME_THRESHOLD_FACTOR and (current_time - last_kick_time) > KICK_DETECTION_INTERVAL and current_volume > MINIMUM_VOLUME_THRESHOLD:
        last_kick_time = current_time
        return True
    return False

def main():
    devices = broadlink.discover(timeout=5)
    device = None
    for dev in devices:
        if "RM4 pro" in dev.model:
            dev.auth()
            device = dev
            print("Successfully authenticated with device:", dev.model)
            break
    if device:
        start_show(device)
    else:
        print("No compatible Broadlink device found.")

def start_show(device):
    print("Starting show...")
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK, stream_callback=lambda in_data, frame_count, time_info, status: stream_callback(in_data, frame_count, time_info, status, device))
    stream.start_stream()
    try:
        while stream.is_active():
            pass
    except KeyboardInterrupt:
        stop_show(stream, audio)

def stream_callback(in_data, frame_count, time_info, status, device):
    global last_kick_time
    audio_data = np.frombuffer(in_data, dtype=np.int16)
    volume = np.linalg.norm(audio_data) * 10
    update_volume_average(volume)
    current_time = time.time()
    if is_kick_detected(volume, average_volume, current_time):
        print(f"Kick detected! Volume: {volume} | Time: {current_time}")
        send_rf_signal(device)  # Assurez-vous que cette fonction est correctement définie pour envoyer votre signal RF.
    return (in_data, pyaudio.paContinue)

def stop_show(stream, audio):
    stream.stop_stream()
    stream.close()
    audio.terminate()
    print("Show stopped.")

OFF_SIGNAL = "b1c0a400ce9e06001421290b290d280d280e280d270e270e270f270e270e270e2610200404102213260f260f0c2a0b290c290c280e280d28280d0d280e00018d280e270e280d280d280d280e280d280d270e270f270e270e270e270f260f270e0c280e270e280d280d280d28280e0d280c00018f280d280d280e270e270d280d280e270e280d280d280d280e280d2710250e270f0c290c290c280e270e280d28280d0d280e0005dc0000"
ON_SIGNAL = "b1c09c00a69e06001420290d280d280c280f270e270e270e270f270e270e260f23131c191db60d290c280d280e280d28280d280d0e00018d280e270e280d280d280d280e270e270e270e270f270e270e270d280f260e280d0d280e270e280d280d280d27280e270e0d00018f280c290c290d270e280d280d280d280e280d280d280d270f270e270e270e270f0c290c280d280e270e280d28280d280d0e0005dc00000000000000000000"

is_on = False

def send_rf_signal(device):
    global is_on  # Indiquez que nous utilisons la variable globale ici
    if is_on:
        print("Sending OFF signal...")
        device.send_data(bytes.fromhex(OFF_SIGNAL))
    else:
        print("Sending ON signal...")
        device.send_data(bytes.fromhex(ON_SIGNAL))
    is_on = not is_on  # Basculez l'état pour la prochaine fois


if __name__ == "__main__":
    main()
