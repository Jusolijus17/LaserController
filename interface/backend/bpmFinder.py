import librosa
import sounddevice as sd
import numpy as np
import requests
import time

SEGMENT_DURATION = 5  # Durée du segment audio à enregistrer en secondes

def record_audio(duration=5, sample_rate=22050):
    """Enregistre l'audio du microphone."""
    print("Enregistrement en cours...")
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
    sd.wait()  # Attend la fin de l'enregistrement
    return recording.flatten()

def estimate_tempo(audio_data, sample_rate=22050):
    """Estime le tempo de l'audio enregistré."""
    onset_env = librosa.onset.onset_strength(y=audio_data, sr=sample_rate)
    tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sample_rate)
    return tempo

def send_bpm_to_server(bpm):
    """Envoie le BPM calculé au serveur via une requête HTTP POST."""
    url = 'http://127.0.0.1:5000/update_bpm'  # Assurez-vous que cette URL correspond à votre configuration Flask
    data = {'bpm': bpm}
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print(f"Tempo {bpm} BPM envoyé avec succès au serveur.")
        else:
            print(f"Erreur lors de l'envoi du tempo au serveur: {response.status_code}")
    except requests.RequestException as e:
        print(f"Erreur de connexion au serveur: {e}")

def continuous_tempo_estimation(segment_duration=SEGMENT_DURATION):
    """Effectue une estimation continue du tempo et envoie les résultats au serveur."""
    print("Début de l'analyse continue du tempo. Appuyez sur Ctrl+C pour arrêter.")
    try:
        while True:
            audio_data = record_audio(duration=segment_duration)
            tempo = estimate_tempo(audio_data)
            print(f"Tempo estimé : {tempo} BPM")
            send_bpm_to_server(tempo)
            time.sleep(segment_duration)  # Attend avant d'enregistrer le prochain segment
    except KeyboardInterrupt:
        print("Arrêt de l'analyse continue du tempo.")

if __name__ == '__main__':
    continuous_tempo_estimation()
