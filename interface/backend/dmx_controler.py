import socket
import threading
import time
import requests
from constants import PATTERNS

# Configuration du socket
host = 'localhost'  # Correspond à l'adresse utilisée par le script de détection de tempo
port = 65432  # Le même port que celui utilisé par le script de détection de tempo
olad_ip = '192.168.2.52'
olad_port = 9090
universe = 1

should_send_dmx = False

# Variable globale pour stocker le tempo
current_tempo = 90  # Valeur initiale de tempo

def listen_for_tempo():
    """Écoute les mises à jour de tempo envoyées par le script de détection de tempo."""
    global current_tempo
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, port))
        sock.listen()
        
        while True:
            connection, _ = sock.accept()
            with connection:
                while True:
                    data = connection.recv(1024)
                    if not data:
                        break
                    current_tempo = float(data.decode())
                    print(f"Nouveau tempo reçu : {current_tempo} BPM")

def send_dmx_at_bpm():
    pattern_index = 0
    next_time = time.time()
    patterns = [f'255,${PATTERNS[0]}', f'255,${PATTERNS[1]}', f'255,${PATTERNS[2]}', f'255,${PATTERNS[3]}']
    while should_send_dmx:
        if current_tempo > 0:
            delay = (60.0 / current_tempo) * 4  # Pour chaque quart de BPM
            next_time += delay  # Planifie le prochain envoi
            
            # Prépare et envoie la requête
            payload = {'u': universe, 'd': patterns[pattern_index]}
            url = f'http://{olad_ip}:{olad_port}/set_dmx'
            try:
                requests.post(url, data=payload)
                print(f"Pattern {pattern_index} sent")
            except requests.RequestException as e:
                print(f"Failed to send DMX data: {e}")
            
            pattern_index = (pattern_index + 1) % len(patterns)
            
            # Ajuste le sleep pour correspondre au prochain temps planifié
            time.sleep(max(0, next_time - time.time()))

def start_sending_dmx():
    global should_send_dmx
    should_send_dmx = True
    print("Démarrage de l'envoi de DMX")
    dmx_sender_thread = threading.Thread(target=send_dmx_at_bpm)
    dmx_sender_thread.start()

def stop_sending_dmx():
    global should_send_dmx
    should_send_dmx = False


if __name__ == "__main__":
    # Démarrer un thread pour écouter le tempo
    tempo_listener_thread = threading.Thread(target=listen_for_tempo)
    tempo_listener_thread.start()
    tempo_listener_thread.join()
