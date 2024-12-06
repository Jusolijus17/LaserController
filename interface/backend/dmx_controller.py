from email.policy import default
import time
import requests
from constants import *
from cue import Cue

class DMXController:
    def __init__(self, dmx_values, olad_ip='192.168.2.52', olad_port=9090, universe=1):
        self.olad_ip = olad_ip
        self.olad_port = olad_port
        self.universe = universe
        self.current_tempo = 90  # Valeur initiale de tempo
        self.should_send_dmx = False
        self.patterns_list = list(LASER_PATTERNS.values())
        self.color_list = list(LASER_COLORS.values())
        self.included_lights_color = list()
        self.pattern_index = 0
        self.color_index = 0
        self.next_time = time.time()
        self.dmx_values = dmx_values
        self.sync_modes = set()
        self.multiplier = 1
        self.strobe_mode = False
        self.pause_dmx_send = False

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
    
    def set_laser_pattern_include(self, include_list):
        """Ajoute un pattern à la liste de patterns à synchroniser."""
        for pattern in include_list:
            pattern_value = LASER_PATTERNS.get(pattern['name'], next(iter(LASER_PATTERNS.values())))
            should_include = pattern['include']
            if should_include and pattern_value not in self.patterns_list:
                self.patterns_list.append(pattern_value)
            elif not should_include and pattern_value in self.patterns_list:
                self.pattern_index = 0
                self.patterns_list.remove(pattern_value)
    
    def set_lights_include_color(self, included_lights):
        """Ajoute une lumière à la liste de lumière à changer de couleur."""
        self.included_lights_color = included_lights

    def set_blackout(self, enabled):
        """Active ou désactive le laser."""
        self.dmx_values[LASER_CHANNELS['mode']] = LASER_MODES['blackout'] if enabled else LASER_MODES['manual']
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
                    self.update_dmx_channels()
                    self.set_blackout(laser_on)
                    time.sleep(max(0, next_on_time - time.time()))  # Attend jusqu'à la prochaine activation
                    self.set_blackout(not laser_on)
                    self.next_time = next_off_time
                    time.sleep(max(0, self.next_time - time.time()))  # Attend jusqu'à la prochaine désactivation
                else:
                    self.update_dmx_channels()
                    self.next_time += full_cycle
                    time.sleep(max(0, self.next_time - time.time()))  # Attend jusqu'au prochain cycle complet

    def update_dmx_channels(self):
        """Mise à jour des canaux DMX sans modification du laser."""
        if 'pattern' in self.sync_modes:
            self.dmx_values[LASER_CHANNELS['pattern']] = self.patterns_list[self.pattern_index]
            self.pattern_index = (self.pattern_index + 1) % len(self.patterns_list)
        if 'color' in self.sync_modes:
            self.dmx_values[LASER_CHANNELS['color']] = self.color_list[self.color_index]
            self.color_index = (self.color_index + 1) % len(self.color_list)
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

    def set_vertical_adjust(self, value):
        """Définit l'ajustement vertical."""
        self.dmx_values[LASER_CHANNELS['vertical movement']] = value
        self.send_request()

    def set_laser_mode(self, mode):
        """Définit le mode de fonctionnement."""
        default_mode = next(iter(LASER_MODES.values()))
        self.dmx_values[LASER_CHANNELS['mode']] = LASER_MODES.get(mode, default_mode)
        if mode != 'manual':
            self.should_send_dmx = False
        self.send_request()

    def set_laser_pattern(self, pattern):
        """Définit le pattern."""
        default_pattern = next(iter(LASER_PATTERNS.values()))
        self.dmx_values[LASER_CHANNELS['pattern']] = LASER_PATTERNS.get(pattern, default_pattern)
        self.send_request()
    
    def set_color(self, color):
        """Définit la couleur."""
        default_laser_color = next(iter(LASER_COLORS.values()))
        default_mh_color = next(iter(MOVING_HEAD_COLORS.values()))
        if self.get_light_control_color_target() == 'laser':
            print("Changing laser color: ", color)
            self.dmx_values[LASER_CHANNELS['color']] = LASER_COLORS.get(color, default_laser_color)
        elif self.get_light_control_color_target() == 'movingHead':
            print("Changing moving head color: ", color)
            self.dmx_values[MOVING_HEAD_CHANNELS['color']] = MOVING_HEAD_COLORS.get(color, default_mh_color)
        elif self.get_light_control_color_target() == 'both':
            print("Changing both laser and moving head color: ", color)
            self.dmx_values[LASER_CHANNELS['color']] = LASER_COLORS.get(color, default_laser_color)
            self.dmx_values[MOVING_HEAD_CHANNELS['color']] = MOVING_HEAD_COLORS.get(color, default_mh_color)
        self.send_request()

    def set_horizontal_animation(self, enabled, speed):
        """Définit l'animation horizontale."""
        if enabled:
            self.dmx_values[LASER_CHANNELS['horizontal movement']] = speed
        else:
            self.dmx_values[LASER_CHANNELS['horizontal movement']] = 0
        self.send_request()

    def set_vertical_animation(self, enabled, speed):
        """Définit l'animation verticale."""
        if enabled:
            self.dmx_values[LASER_CHANNELS['vertical movement']] = speed
        else:
            self.dmx_values[LASER_CHANNELS['vertical movement']] = 0
        self.send_request()

    def send_request(self):
        if self.pause_dmx_send:
            return
        dmx_values_str = ','.join(map(str, self.dmx_values))
        url = f'http://{self.olad_ip}:{self.olad_port}/set_dmx'
        payload = {'u': self.universe, 'd': dmx_values_str}
        response = requests.post(url, data=payload)
        return response

    def stop_sending_dmx(self):
        """Arrête l'envoi de données DMX."""
        self.should_send_dmx = False
        print("Arrêt de l'envoi de DMX")

    def set_mh_mode(self, mode):
        """Définit le mode de fonctionnement du Moving Head."""
        if mode == 'blackout':
            self.dmx_values[MOVING_HEAD_CHANNELS['dimming']] = 0
            self.dmx_values[MOVING_HEAD_CHANNELS['pan running']] = 0
            self.dmx_values[MOVING_HEAD_CHANNELS['tilt running']] = 0
        self.dmx_values[MOVING_HEAD_CHANNELS['mode']] = MOVING_HEAD_MODES.get(mode, next(iter(MOVING_HEAD_MODES.values())))
        self.send_request()

    def set_mh_scene(self, scene):
        """Définit la scène du Moving Head."""
        if scene == 'slow':
            self.dmx_values[MOVING_HEAD_CHANNELS['auto mode']] = MOVING_HEAD_AUTO['panTilt']
            self.dmx_values[MOVING_HEAD_CHANNELS['running speed']] = MOVING_HEAD_SLOW_RUNNING
        elif scene == 'medium':
            self.dmx_values[MOVING_HEAD_CHANNELS['auto mode']] = MOVING_HEAD_AUTO['panTilt']
            self.dmx_values[MOVING_HEAD_CHANNELS['running speed']] = MOVING_HEAD_MEDIUM_RUNNING
            self.dmx_values[MOVING_HEAD_CHANNELS['gobo']] = MOVING_HEAD_MEDIUM_GOBO
        elif scene == 'fast':
            self.dmx_values[MOVING_HEAD_CHANNELS['auto mode']] = MOVING_HEAD_AUTO['panTilt']
            self.dmx_values[MOVING_HEAD_CHANNELS['running speed']] = MOVING_HEAD_FAST_RUNNING
            self.dmx_values[MOVING_HEAD_CHANNELS['gobo']] = MOVING_HEAD_FAST_GOBO
        else:
            self.dmx_values[MOVING_HEAD_CHANNELS['auto mode']] = 0
            self.dmx_values[MOVING_HEAD_CHANNELS['running speed']] = 0
            self.dmx_values[MOVING_HEAD_CHANNELS['color']] = MOVING_HEAD_COLORS['red']
            self.dmx_values[MOVING_HEAD_CHANNELS['gobo']] = 0
        self.send_request()

    def set_mh_brightness(self, dimmer):
        """Définit le dimmer du Moving Head."""
        value = int((dimmer / 100.0) * 255)
        print("Setting dimmer to ", value)
        self.dmx_values[MOVING_HEAD_CHANNELS['dimming']] = value
        self.send_request()

    def send_single_strobe(self):
        """Envoie un seul flash stroboscopique."""
        previous_dimmer = self.dmx_values[MOVING_HEAD_CHANNELS['dimming']]
        previous_color = self.dmx_values[MOVING_HEAD_CHANNELS['color']]

        self.dmx_values[MOVING_HEAD_CHANNELS['dimming']] = 255
        self.dmx_values[MOVING_HEAD_CHANNELS['color']] = MOVING_HEAD_COLORS['white']
        self.send_request()

        time.sleep(0.1)

        self.dmx_values[MOVING_HEAD_CHANNELS['dimming']] = previous_dimmer
        self.dmx_values[MOVING_HEAD_CHANNELS['color']] = previous_color
        self.send_request()

    def start_mh_strobe(self):
        """Démarre le mode stroboscopique du Moving Head."""
        global previous_strobe
        previous_strobe = self.dmx_values[MOVING_HEAD_CHANNELS['strobe']]
        global previous_color
        previous_color = self.dmx_values[MOVING_HEAD_CHANNELS['color']]

        self.dmx_values[MOVING_HEAD_CHANNELS['color']] = MOVING_HEAD_COLORS['white']
        self.dmx_values[MOVING_HEAD_CHANNELS['strobe']] = 220
        self.send_request()

    def stop_mh_strobe(self):
        """Arrête le mode stroboscopique du Moving Head."""
        self.dmx_values[MOVING_HEAD_CHANNELS['color']] = previous_color
        self.dmx_values[MOVING_HEAD_CHANNELS['strobe']] = 0
        self.send_request()

    def set_mh_strobe(self, value):
        """Définit la fréquence du stroboscope du Moving Head."""
        amount = int((value / 100.0) * 255)
        self.dmx_values[MOVING_HEAD_CHANNELS['strobe']] = amount
        self.send_request()

    def set_mh_color_speed(self, speed):
        """Définit la vitesse de changement de couleur du Moving Head."""
        if speed == 0:
            speed = MOVING_HEAD_COLORS['red']
        else:
            speed = int(140 + (speed / 100.0) * (255 - 140))
        self.dmx_values[MOVING_HEAD_CHANNELS['color']] = speed
        self.send_request()

    def get_light_control_color_target(self):
        """Récupère la couleur cible des lumières."""
        if len(self.included_lights_color) == 1 and self.included_lights_color[0] == 'Laser':
            return 'laser'
        elif len(self.included_lights_color) == 1 and self.included_lights_color[0] == 'Moving Head':
            return 'movingHead'
        elif len(self.included_lights_color) == 2:
            return 'both'
        else:
            return 'none'
        
    def set_pan_tilt(self, pan, tilt):
        """
        Met à jour les canaux DMX pour Pan et Tilt.
        """
        # Conversion de Pan en valeur DMX
        dmx_pan = int((pan + 180) / 360 * 170)  # Remap à [0, 170]
        # Conversion de Tilt en valeur DMX
        if tilt > 0:
            dmx_tilt = int((tilt) / 180 * 255)  # Remap à [0, 255]
        else:
            dmx_tilt = 0
        self.dmx_values[MOVING_HEAD_CHANNELS['pan running']] = dmx_pan  # Canal DMX 1 pour Pan Fine
        self.dmx_values[MOVING_HEAD_CHANNELS['tilt running']] = dmx_tilt  # Canal DMX 2 pour Tilt Fine
        self.send_request()
        
    def set_mh_color(self, color):
        """
        Définit la couleur du Moving Head.
        """
        default_mh_color = next(iter(MOVING_HEAD_COLORS.values()))
        self.dmx_values[MOVING_HEAD_CHANNELS['color']] = MOVING_HEAD_COLORS.get(color, default_mh_color)
        self.send_request()
        
    def set_laser_color(self, color):
        """
        Définit la couleur du laser.
        """
        default_laser_color = next(iter(LASER_COLORS.values()))
        self.dmx_values[LASER_CHANNELS['color']] = LASER_COLORS.get(color, default_laser_color)
        self.send_request()
        
    def set_cue(self, cue: Cue):
        """
        Définit la valeur de la cue.
        """
        self.pause_dmx_send = True
        if cue.includeLaser:
            self.set_laser_mode(cue.laserMode)
            self.set_sync_modes(cue.laserBPMSyncModes)
            self.set_laser_color(cue.laserColor)
            self.set_laser_pattern(cue.laserPattern)
            self.set_laser_pattern_include(cue.laserIncludedPatterns)
        if cue.includeMovingHead:
            self.set_mh_mode(cue.movingHeadMode)
            self.set_mh_color_speed(cue.movingHeadColorFrequency)
            self.set_mh_scene(cue.movingHeadScene)
            self.set_mh_color(cue.movingHeadColor)
            print(cue.movingHeadColor)
            self.set_mh_strobe(cue.movingHeadStrobeFrequency)
            self.set_mh_brightness(cue.movingHeadBrightness)
            if cue.positionPreset:
                self.set_pan_tilt(cue.positionPreset['pan'], cue.positionPreset['tilt'])
        self.pause_dmx_send = False
        self.send_request()
