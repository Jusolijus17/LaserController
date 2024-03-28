from email.policy import default
import time
import requests
from constants import PATTERNS, COLORS, CHANNELS, MODES

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
        self.multiplier = 1

    def update_tempo(self, tempo):
        """Mise à jour du tempo."""
        self.current_tempo = tempo
        print(f"Nouveau tempo reçu : {self.current_tempo} BPM")

    def set_multiplier(self, multiplier):
        """Définit le multiplicateur de tempo."""
        self.multiplier = multiplier

    def send_dmx_at_bpm(self):
        """Envoie les valeurs DMX à l'intervalle calculé selon le BPM."""
        while self.should_send_dmx:
            if self.current_tempo > 0:
                delay = (60.0 / self.current_tempo) * self.multiplier
                self.next_time += delay  # Planifie le prochain envoi
                
                if 'pattern' in self.sync_modes:
                    self.dmx_values[CHANNELS['pattern']] = self.patterns_list[self.pattern_index]
                    self.pattern_index = (self.pattern_index + 1) % len(self.patterns_list)
                if 'color' in self.sync_modes:
                    self.dmx_values[CHANNELS['color']] = self.color_list[self.color_index]
                    self.color_index = (self.color_index + 1) % len(self.color_list)

                self.send_request()

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

    def set_horizontal_adjust(self, value):
        """Définit l'ajustement horizontal."""
        self.dmx_values[CHANNELS['vertical movement']] = value
        self.send_request()

    def set_mode(self, mode):
        """Définit le mode de fonctionnement."""
        default_mode = next(iter(MODES.values()))
        self.dmx_values[CHANNELS['mode']] = MODES.get(mode, default_mode)
        self.send_request()

    def set_pattern(self, pattern):
        """Définit le pattern."""
        default_pattern = next(iter(PATTERNS.values()))
        self.dmx_values[CHANNELS['pattern']] = PATTERNS.get(pattern, default_pattern)
        self.send_request()
    
    def set_color(self, color):
        """Définit la couleur."""
        default_color = next(iter(COLORS.values()))
        self.dmx_values[CHANNELS['color']] = COLORS.get(color, default_color)
        self.send_request()

    def set_horizontal_animation(self, enabled, speed):
        """Définit l'animation horizontale."""
        if enabled:
            self.dmx_values[CHANNELS['horizontal movement']] = speed
        else:
            self.dmx_values[CHANNELS['horizontal movement']] = 0
        self.send_request()

    def set_vertical_animation(self, enabled, speed):
        """Définit l'animation verticale."""
        if enabled:
            self.dmx_values[CHANNELS['vertical movement']] = speed
        else:
            self.dmx_values[CHANNELS['vertical movement']] = 0
        self.send_request()

    def send_request(self):
        dmx_values_str = ','.join(map(str, self.dmx_values))
        url = f'http://{self.olad_ip}:{self.olad_port}/set_dmx'
        payload = {'u': self.universe, 'd': dmx_values_str}
        response = requests.post(url, data=payload)
        return response

    def stop_sending_dmx(self):
        """Arrête l'envoi de données DMX."""
        self.should_send_dmx = False
