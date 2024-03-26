import time
import requests
from constants import PATTERNS, COLORS, CHANNELS

class DMXController:
    def __init__(self, dmx_values, olad_ip='192.168.2.52', olad_port=9090, universe=1):
        self.olad_ip = olad_ip
        self.olad_port = olad_port
        self.universe = universe
        self.current_tempo = 90  # Valeur initiale de tempo
        self.should_send_dmx = False
        self.patterns_list = list(PATTERNS.values())
        self.color_list = list(COLORS.values())
        self.pattern_index = 0
        self.color_index = 0
        self.next_time = time.time()
        self.dmx_values = dmx_values
        self.sync_modes = set()

    def update_tempo(self, tempo):
        """Mise à jour du tempo."""
        self.current_tempo = tempo
        print(f"Nouveau tempo reçu : {self.current_tempo} BPM")

    def send_dmx_at_bpm(self):
        """Envoie les valeurs DMX à l'intervalle calculé selon le BPM."""
        while self.should_send_dmx:
            if self.current_tempo > 0:
                delay = (60.0 / self.current_tempo) * 4  # Pour chaque quart de BPM
                self.next_time += delay  # Planifie le prochain envoi
                
                if 'pattern' in self.sync_modes:
                    self.dmx_values[CHANNELS['pattern']] = self.patterns_list[self.pattern_index]
                    self.pattern_index = (self.pattern_index + 1) % len(self.patterns_list)
                if 'color' in self.sync_modes:
                    self.dmx_values[CHANNELS['color']] = self.color_list[self.color_index]
                    self.color_index = (self.color_index + 1) % len(self.color_list)

                dmx_values_str = ','.join(map(str, self.dmx_values))
                payload = {'u': self.universe, 'd': dmx_values_str}
                url = f'http://{self.olad_ip}:{self.olad_port}/set_dmx'
                try:
                    requests.post(url, data=payload)
                    print("Current tempo: ", self.current_tempo)
                except requests.RequestException as e:
                    print(f"Failed to send DMX data: {e}")

                # Ajuste le sleep pour correspondre au prochain temps planifié
                time.sleep(max(0, self.next_time - time.time()))

    def start_sending_dmx(self, modes):
        """Démarre l'envoi de données DMX selon le tempo."""
        self.sync_modes = set(modes)
        if not self.should_send_dmx:
            self.should_send_dmx = True
            self.next_time = time.time()
            print("Démarrage de l'envoi de DMX")
            from threading import Thread
            dmx_sender_thread = Thread(target=self.send_dmx_at_bpm)
            dmx_sender_thread.start()

    def stop_sending_dmx(self):
        """Arrête l'envoi de données DMX."""
        self.should_send_dmx = False