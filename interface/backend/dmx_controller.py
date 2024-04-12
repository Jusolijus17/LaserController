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
        self.strobe_mode = False

    def update_tempo(self, tempo):
        """Mise à jour du tempo."""
        self.current_tempo = tempo
        print(f"Nouveau tempo reçu : {self.current_tempo} BPM")

    def set_multiplier(self, multiplier):
        """Définit le multiplicateur de tempo."""
        self.multiplier = multiplier

    def set_strobe_mode(self, enabled):
        """Active ou désactive le mode stroboscopique."""
        self.strobe_mode = enabled
        self.start_sending_dmx()

    def set_sync_modes(self, modes):
        """Définit les modes à synchroniser."""
        self.sync_modes = set(modes)
        self.start_sending_dmx()

    def set_blackout(self, enabled):
        """Active ou désactive le laser."""
        self.dmx_values[CHANNELS['mode']] = MODES['blackout'] if enabled else MODES['manual']
        self.send_request()

    def send_dmx_at_bpm(self):
        """Envoie les valeurs DMX à l'intervalle calculé selon le BPM."""
        laser_on = True  # Commence avec le laser allumé
        while self.should_send_dmx:
            if self.current_tempo > 0:
                full_cycle = (60.0 / self.current_tempo) * self.multiplier
                on_time = full_cycle * 0.5
                off_time = full_cycle - on_time
                next_on_time = self.next_time + on_time
                next_off_time = next_on_time + off_time

                if self.strobe_mode:
                    # Alterne le laser entre allumé et éteint
                    self.update_dmx_channels(double_update=False)
                    self.set_blackout(laser_on)
                    time.sleep(max(0, next_on_time - time.time()))  # Attend jusqu'à la prochaine activation
                    self.set_blackout(not laser_on)
                    self.next_time = next_off_time
                    time.sleep(max(0, self.next_time - time.time()))  # Attend jusqu'à la prochaine désactivation
                else:
                    self.update_dmx_channels()
                    self.next_time += full_cycle
                    time.sleep(max(0, self.next_time - time.time()))  # Attend jusqu'au prochain cycle complet

    def update_dmx_channels(self, double_update=False):
        """Mise à jour des canaux DMX sans modification du laser."""
        if 'pattern' in self.sync_modes:
            self.dmx_values[CHANNELS['pattern']] = self.patterns_list[self.pattern_index]
            self.pattern_index = (self.pattern_index + 1) % len(self.patterns_list)
        if 'color' in self.sync_modes:
            self.dmx_values[CHANNELS['color']] = self.color_list[self.color_index]
            self.color_index = (self.color_index + 1) % len(self.color_list)
        if not double_update:
            self.send_request()

    def start_sending_dmx(self):
        """Démarre l'envoi de données DMX selon le tempo."""
        if not self.sync_modes and not self.strobe_mode:
            self.stop_sending_dmx()
            return
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
        if mode != 'manual':
            self.should_send_dmx = False
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
        print("Arrêt de l'envoi de DMX")
