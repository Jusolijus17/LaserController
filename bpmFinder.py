import librosa
import sounddevice as sd
import numpy as np
import socketio
import time

SEGMENT_DURATION = 5

sio = socketio.Client()

def record_audio(duration=5, sample_rate=22050):
    """Enregistre l'audio du microphone."""
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
    sd.wait()  # Attend la fin de l'enregistrement
    return recording.flatten()

def estimate_tempo(audio_data, sample_rate=22050):
    """Estime le tempo de l'audio enregistré."""
    onset_env = librosa.onset.onset_strength(y=audio_data, sr=sample_rate)
    tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sample_rate)
    return tempo

@sio.event
def connect():
    print('Connection établie avec le serveur SocketIO.')

@sio.event
def disconnect():
    print('Déconnecté du serveur SocketIO.')

sio.connect('http://127.0.0.1:5000')

def continuous_tempo_estimation_with_socket(segment_duration=5):
    print("Début de l'analyse continue du tempo. Appuyez sur Ctrl+C pour arrêter.")
    try:
        while True:
            audio_data = record_audio(duration=segment_duration)
            tempo = estimate_tempo(audio_data)
            print(f"Tempo estimé : {tempo} BPM")

            # Envoyez le tempo au serveur Flask via SocketIO
            sio.emit('tempo_update', {'tempo': tempo})

            time.sleep(segment_duration)
    except KeyboardInterrupt:
        print("Arrêt de l'analyse continue.")

if __name__ == '__main__':
    continuous_tempo_estimation_with_socket(SEGMENT_DURATION)
