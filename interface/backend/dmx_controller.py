from email.policy import default
import time
from xml.etree.ElementInclude import include
import requests
from constants import *
from classes.Cue import Cue
from threading import Thread

class DMXController:
    def __init__(self, dmx_values, olad_ip='192.168.2.52', olad_port=9090, universe=1):
        self.olad_ip = olad_ip
        self.olad_port = olad_port
        self.universe = universe
        self.current_tempo = 90  # Valeur initiale de tempo
        self.should_send_dmx = False
        self.should_breathe = False
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
        self.included_lights_strobe = list()
        self.pause_dmx_send = False

    def update_tempo(self, tempo):
        """Mise à jour du tempo."""
        self.current_tempo = tempo
        print(f"Nouveau tempo reçu : {self.current_tempo} BPM")

    def set_multiplier(self, multiplier):
        """Définit le multiplicateur de tempo."""
        self.multiplier = multiplier

    def set_strobe_mode(self, enabled, light):
        """Active ou désactive le mode stroboscopique."""
        if enabled:
            if light not in self.included_lights_strobe:
                self.included_lights_strobe.append(light)
        else:
            if light in self.included_lights_strobe:
                self.included_lights_strobe.remove(light)
        self.start_sending_dmx()

    def set_sync_modes(self, modes):
        """Définit les modes à synchroniser."""
        self.sync_modes = set(modes)
        self.start_sending_dmx()
        
    def add_sync_mode(self, mode):
        """Ajoute un mode à synchroniser."""
        self.sync_modes.add(mode)
        self.start_sending_dmx()
        
    def remove_sync_mode(self, mode):
        """Supprime un mode à synchroniser."""
        if mode in self.sync_modes:
            self.sync_modes.remove(mode)
            self.start_sending_dmx()
    
    def set_laser_pattern_include(self, include_list):
        """Ajoute un pattern à la liste de patterns à synchroniser."""
        self.pattern_index = 0
        self.patterns_list = include_list
        # for pattern in include_list:
        #     pattern_value = LASER_PATTERNS.get(pattern, next(iter(LASER_PATTERNS.values())))
        #     should_include = pattern['include']
        #     if should_include and pattern_value not in self.patterns_list:
        #         self.patterns_list.append(pattern_value)
        #     elif not should_include and pattern_value in self.patterns_list:
        #         self.pattern_index = 0
        #         self.patterns_list.remove(pattern_value)
    
    def set_lights_include_color(self, included_lights):
        """Ajoute une lumière à la liste de lumière à changer de couleur."""
        self.included_lights_color = included_lights

    def set_blackout(self, enabled, light):
        """Active ou désactive le laser."""
        if light == 'laser':
            self.dmx_values[LASER_CHANNELS['mode']] = LASER_MODES['blackout'] if enabled else LASER_MODES['manual']
        elif light == 'movingHead':
            self.dmx_values[MOVING_HEAD_CHANNELS['dimming']] = 0 if enabled else 255
        self.send_request()

    def send_dmx_at_bpm(self):
        """Envoie les valeurs DMX à l'intervalle calculé selon le BPM."""
        while self.should_send_dmx:
            if self.current_tempo > 0:
                full_cycle = (60.0 / self.current_tempo) * self.multiplier
                on_time = full_cycle * 0.5
                off_time = full_cycle - on_time
                next_on_time = self.next_time + on_time
                next_off_time = next_on_time + off_time

                if self.included_lights_strobe:
                    # Alterne le laser entre allumé et éteint
                    self.update_dmx_channels()
                    if 'laser' in self.included_lights_strobe:
                        self.set_blackout(True, 'laser')
                    if 'movingHead' in self.included_lights_strobe:
                        self.set_blackout(True, 'movingHead')
                    time.sleep(max(0, next_on_time - time.time()))  # Attend jusqu'à la prochaine activation
                    if 'laser' in self.included_lights_strobe:
                        self.set_blackout(False, 'laser')
                    if 'movingHead' in self.included_lights_strobe:
                        self.set_blackout(False, 'movingHead')
                    self.next_time = next_off_time
                    time.sleep(max(0, self.next_time - time.time()))  # Attend jusqu'à la prochaine désactivation
                else:
                    self.update_dmx_channels()
                    self.next_time += full_cycle
                    time.sleep(max(0, self.next_time - time.time()))  # Attend jusqu'au prochain cycle complet

    def update_dmx_channels(self):
        """Mise à jour des canaux DMX sans modification du laser."""
        if 'pattern' in self.sync_modes:
            self.dmx_values[LASER_CHANNELS['pattern']] = LASER_PATTERNS.get(self.patterns_list[self.pattern_index], next(iter(LASER_PATTERNS.values())))
            self.pattern_index = (self.pattern_index + 1) % len(self.patterns_list)
        if 'color' in self.sync_modes:
            self.dmx_values[LASER_CHANNELS['color']] = self.color_list[self.color_index]
            self.color_index = (self.color_index + 1) % len(self.color_list)
        self.send_request()

    def start_sending_dmx(self):
        """Démarre l'envoi de données DMX selon le tempo."""
        if not self.sync_modes and not self.included_lights_strobe:
            self.stop_sending_dmx()
            return
        if not self.should_send_dmx:
            self.should_send_dmx = True
            self.next_time = time.time()
            print("Démarrage de l'envoi de DMX")
            dmx_sender_thread = Thread(target=self.send_dmx_at_bpm)
            dmx_sender_thread.start()

    def set_vertical_adjust(self, value):
        """Définit l'ajustement vertical."""
        self.dmx_values[LASER_CHANNELS['vertical movement']] = value
        self.send_request()

    def set_mode_for(self, light, mode):
        """Définit le mode de fonctionnement."""
        if light == 'laser':
            default_mode = next(iter(LASER_MODES.values()))
            self.dmx_values[LASER_CHANNELS['mode']] = LASER_MODES.get(mode, default_mode)
            if mode != 'manual':
                self.should_send_dmx = False
        elif light == 'movingHead':
            if mode == 'blackout':
                self.dmx_values[MOVING_HEAD_CHANNELS['dimming']] = 0
                self.dmx_values[MOVING_HEAD_CHANNELS['pan running']] = 0
                self.dmx_values[MOVING_HEAD_CHANNELS['tilt running']] = 0
                self.set_mh_breathe(False)
            self.dmx_values[MOVING_HEAD_CHANNELS['mode']] = MOVING_HEAD_MODES.get(mode, next(iter(MOVING_HEAD_MODES.values())))
        self.send_request()

    def set_laser_pattern(self, pattern):
        """Définit le pattern."""
        default_pattern = next(iter(LASER_PATTERNS.values()))
        self.dmx_values[LASER_CHANNELS['pattern']] = LASER_PATTERNS.get(pattern, default_pattern)
        self.send_request()
    
    def set_color(self, color, light):
        """Définit la couleur."""
        if light == 'laser':
            print("Changing laser color: ", color)
            self.set_laser_color(color)
        elif light == 'movingHead':
            print("Changing moving head color: ", color)
            self.set_mh_color(color)
        elif light == 'both':
            print("Changing both laser and moving head color: ", color)
            self.set_laser_color(color)
            self.set_mh_color(color)
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

    def set_mh_scene(self, scene):
        print("Setting scene to: ", scene)
        """Définit la scène du Moving Head."""
        if scene == 'slow':
            self.dmx_values[MOVING_HEAD_CHANNELS['pan running']] = 0
            self.dmx_values[MOVING_HEAD_CHANNELS['tilt running']] = 0
            self.dmx_values[MOVING_HEAD_CHANNELS['auto mode']] = MOVING_HEAD_AUTO['panTilt']
            self.dmx_values[MOVING_HEAD_CHANNELS['running speed']] = MOVING_HEAD_SLOW_RUNNING
        elif scene == 'medium':
            self.dmx_values[MOVING_HEAD_CHANNELS['pan running']] = 0
            self.dmx_values[MOVING_HEAD_CHANNELS['tilt running']] = 0
            self.dmx_values[MOVING_HEAD_CHANNELS['auto mode']] = MOVING_HEAD_AUTO['panTilt']
            self.dmx_values[MOVING_HEAD_CHANNELS['running speed']] = MOVING_HEAD_MEDIUM_RUNNING
            self.dmx_values[MOVING_HEAD_CHANNELS['gobo']] = MOVING_HEAD_MEDIUM_GOBO
        elif scene == 'fast':
            self.dmx_values[MOVING_HEAD_CHANNELS['pan running']] = 0
            self.dmx_values[MOVING_HEAD_CHANNELS['tilt running']] = 0
            self.dmx_values[MOVING_HEAD_CHANNELS['auto mode']] = MOVING_HEAD_AUTO['panTilt']
            self.dmx_values[MOVING_HEAD_CHANNELS['running speed']] = MOVING_HEAD_FAST_RUNNING
            self.dmx_values[MOVING_HEAD_CHANNELS['gobo']] = MOVING_HEAD_FAST_GOBO
        elif scene == 'off':
            self.dmx_values[MOVING_HEAD_CHANNELS['pan running']] = 0
            self.dmx_values[MOVING_HEAD_CHANNELS['tilt running']] = 0
            self.dmx_values[MOVING_HEAD_CHANNELS['auto mode']] = 0
            self.dmx_values[MOVING_HEAD_CHANNELS['running speed']] = 0
            self.dmx_values[MOVING_HEAD_CHANNELS['gobo']] = 0
        self.send_request()

    def set_mh_brightness(self, dimmer):
        """Définit le dimmer du Moving Head."""
        value = int((dimmer / 100.0) * 255)
        if value == 0:
            self.set_mh_breathe(False)
        print("Setting dimmer to ", value)
        self.dmx_values[MOVING_HEAD_CHANNELS['dimming']] = value
        self.send_request()
        
    def set_mh_breathe(self, enabled):
        """Définit le mode de respiration du Moving Head."""
        if enabled:
            if not self.should_breathe:
                self.should_breathe = True
                # Vérifie si un thread précédent existe et est terminé
                if hasattr(self, "breathe_thread") and self.breathe_thread.is_alive():
                    self.breathe_thread.join()  # Attends que l'ancien thread se termine proprement
                # Crée un nouveau thread pour le mode breathe
                self.breathe_thread = Thread(target=self.mH_breathe, daemon=True)
                self.breathe_thread.start()
        else:
            self.should_breathe = False
            # Assure que le thread actuel s'arrête proprement
            if hasattr(self, "breathe_thread") and self.breathe_thread.is_alive():
                self.breathe_thread.join()  # Attends que le thread se termine
            print("Effet de respiration arrêté")
            self.send_request()

    def mH_breathe(self):
        """Effectue un effet de respiration (breathe) fluide synchronisé avec le BPM, avec recalibrage pour éviter la désynchronisation."""
        if not self.should_breathe:
            return

        # Temps de référence pour le premier cycle
        reference_time = time.time()

        while self.should_breathe:
            # Calcul de la durée totale du cycle en secondes
            full_cycle = (60.0 / self.current_tempo) * self.multiplier  # Temps pour un cycle complet (BPM ajusté)

            # Étape 1 : Augmente instantanément la luminosité
            self.dmx_values[MOVING_HEAD_CHANNELS['dimming']] = 255
            self.send_request()

            # Étape 2 : Descente progressive immédiatement après
            start_time = time.time()

            while time.time() - start_time <= full_cycle:
                if not self.should_breathe:
                    return  # Arrêt immédiat si demandé

                # Calcul du temps écoulé depuis le début de la descente
                elapsed_time = time.time() - start_time

                # Calcul linéaire de la luminosité décroissante sur toute la durée du cycle
                current_intensity = int(255 * (1 - (elapsed_time / full_cycle)))

                # Applique l'intensité calculée
                self.dmx_values[MOVING_HEAD_CHANNELS['dimming']] = current_intensity
                self.send_request()

            # Recalibrage du temps pour le prochain cycle
            reference_time += full_cycle
            time_to_next_cycle = reference_time - time.time()

            # Attends exactement le temps restant avant le prochain cycle
            if time_to_next_cycle > 0:
                time.sleep(time_to_next_cycle)

    def set_mh_strobe(self, value):
        """Définit la fréquence du stroboscope du Moving Head."""
        amount = int((value / 100.0) * 255)
        self.dmx_values[MOVING_HEAD_CHANNELS['strobe']] = amount
        self.send_request()

    def set_mh_color(self, color = None, speed = 0):
        """Définit la vitesse de changement de couleur du Moving Head."""
        if speed == 0 and color == None:
            self.dmx_values[MOVING_HEAD_CHANNELS['color']] = MOVING_HEAD_COLORS['red']
        elif speed == 0 and color != None:
            default_mh_color = next(iter(MOVING_HEAD_COLORS.values()))
            self.dmx_values[MOVING_HEAD_CHANNELS['color']] = MOVING_HEAD_COLORS.get(color, default_mh_color)
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
        # Arrête le mode automatique
        self.set_mh_scene('off')
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
        print("Setting cue to:", cue)
        self.pause_dmx_send = True

        # Appliquer les réglages pour le Laser
        if "laser" in cue.affectedLights:
            self.set_mode_for("laser", cue.laser.mode)

            for setting in cue.laserSettings:
                if setting == "color":
                    self.set_laser_color(cue.laser.color)
                    if "color" in cue.laser.bpmSyncModes and "color" not in self.sync_modes:
                        self.add_sync_mode("color")
                    elif "color" not in cue.laser.bpmSyncModes and "color" in self.sync_modes:
                        self.remove_sync_mode("color")
                elif setting == "pattern":
                    self.set_laser_pattern(cue.laser.pattern)
                    self.set_laser_pattern_include(list(cue.laser.includedPatterns))
                    if "pattern" in cue.laser.bpmSyncModes and "pattern" not in self.sync_modes:
                        self.add_sync_mode("pattern")
                    elif "pattern" not in cue.laser.bpmSyncModes and "pattern" in self.sync_modes:
                        self.remove_sync_mode("pattern")
                elif setting == "strobe":
                    pass

        # Appliquer les réglages pour les Moving Heads
        if "movingHead" in cue.affectedLights:
            self.set_mode_for("movingHead", cue.movingHead.mode)

            for setting in cue.movingHeadSettings:
                if setting == "color":
                    self.set_mh_color(cue.movingHead.color, cue.movingHead.colorSpeed)
                elif setting == "scene":
                    self.set_mh_scene(cue.movingHead.scene)
                elif setting == "strobeSpeed":
                    self.set_mh_strobe(cue.movingHead.strobeSpeed)
                elif setting == "brightness":
                    self.set_mh_brightness(cue.movingHead.brightness)
                    self.set_mh_breathe(cue.movingHead.breathe)
                elif setting == "position" and cue.movingHead.positionPreset:
                    print("Setting position preset to:", cue.movingHead.positionPreset)
                    self.set_pan_tilt(
                        cue.movingHead.positionPreset["pan"],
                        cue.movingHead.positionPreset["tilt"]
                    )

        self.pause_dmx_send = False
        self.send_request()