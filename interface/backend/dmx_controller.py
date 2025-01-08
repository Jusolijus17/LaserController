import random
import time
from typing import List
from matplotlib.collections import TriMesh
import requests
from constants import *
from classes.Cue import Cue
from threading import Thread, Event
from classes.SpiderHeadState import LEDCell
from classes.StateBackup import BackupVariables, StateBackup

class DMXController:
    def __init__(self, dmx_values, rf_controller, olad_ip='192.168.2.52', olad_port=9090, universe=1):
        self.olad_ip = olad_ip
        self.olad_port = olad_port
        self.universe = universe
        self.dmx_values = dmx_values
        self.rf_controller = rf_controller
        self.current_tempo = 90  # Valeur initiale de tempo
        self.should_send_dmx = False
        self.laser_pattern_include = list(LASER_PATTERNS)
        self.color_list = list(LASER_COLORS.values())
        self.pattern_index = 0
        self.color_index = 0
        self.next_time = time.time()
        self.laser_sync_modes = set()
        self.multiplier = 1
        self.included_lights_strobe = list()
        self.pause_dmx_send = False
        self.should_play_sh_scene = False
        self.laser_vertical_adjust = 0
        self._chase_thread = None             # Référence au thread en cours
        self._chase_stop_event = None         # Event pour arrêter la boucle
        self._current_speed = 0.0 
        self.included_lights_breathe = list()
        self.mh_scene_gobo_switch = True
        self.sh_sync_modes = set()
        self.sh_color_index = 0
        self.backup: StateBackup
        self.sh_scene = 'off'
        self.mh_scene = 'off'
        self.sh_position = None
        self.slow_breathe = True

    def update_tempo(self, tempo):
        """Mise à jour du tempo."""
        self.current_tempo = tempo
        print(f"Nouveau tempo reçu : {self.current_tempo} BPM")

    def set_multiplier(self, multiplier):
        """Définit le multiplicateur de tempo."""
        self.multiplier = multiplier

    def set_strobe_mode(self, included_lights):
        """Active ou désactive le mode stroboscopique."""
        self.included_lights_strobe = included_lights
        self.start_sending_dmx()
        
    def set_strobe_mode_cue(self, light, included_lights):
        """Active ou désactive le mode stroboscopique."""
        if light in included_lights and light not in self.included_lights_strobe:
            self.included_lights_strobe.append(light)
        elif light not in included_lights and light in self.included_lights_strobe:
            self.included_lights_strobe.remove(light)
        self.start_sending_dmx()

    def set_sync_modes_for(self, light, modes):
        """Définit les modes à synchroniser."""
        if light == 'laser':
            self.laser_sync_modes = set(modes)
        elif light == 'spiderHead':
            self.sh_sync_modes = set(modes)
        self.start_sending_dmx()
        
    def add_sync_mode(self, mode):
        """Ajoute un mode à synchroniser."""
        self.laser_sync_modes.add(mode)
        self.start_sending_dmx()
        
    def remove_sync_mode(self, mode):
        """Supprime un mode à synchroniser."""
        if mode in self.laser_sync_modes:
            self.laser_sync_modes.remove(mode)
            self.start_sending_dmx()
    
    def set_laser_pattern_include(self, include_list):
        """Ajoute un pattern à la liste de patterns à synchroniser."""
        self.pattern_index = 0
        self.laser_pattern_include = include_list

    def set_blackout(self, enabled, light):
        """Active ou désactive le laser."""
        if light == 'laser':
            self.dmx_values[LASER_CHANNELS['mode']] = LASER_MODES['blackout'] if enabled else LASER_MODES['manual']
        elif light == 'movingHead':
            self.dmx_values[MOVING_HEAD_CHANNELS['dimming']] = 0 if enabled else 255
        elif light == 'spiderHead':
            self.dmx_values[SPIDER_HEAD_CHANNELS['brightness']] = 0 if enabled else 255
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
                    for light in self.included_lights_strobe:
                        self.set_blackout(True, light)
                    time.sleep(max(0, next_on_time - time.time()))  # Attend jusqu'à la prochaine activation
                    for light in self.included_lights_strobe:
                        self.set_blackout(False, light)
                    self.next_time = next_off_time
                    time.sleep(max(0, self.next_time - time.time()))  # Attend jusqu'à la prochaine désactivation
                else:
                    self.update_dmx_channels()
                    self.next_time += full_cycle
                    time.sleep(max(0, self.next_time - time.time()))  # Attend jusqu'au prochain cycle complet

    def update_dmx_channels(self):
        """Mise à jour des canaux DMX sans modification du laser."""
        if 'pattern' in self.laser_sync_modes:
            self.dmx_values[LASER_CHANNELS['pattern']] = LASER_PATTERNS.get(self.laser_pattern_include[self.pattern_index], next(iter(LASER_PATTERNS.values())))
            self.pattern_index = (self.pattern_index + 1) % len(self.laser_pattern_include)
        if 'color' in self.laser_sync_modes:
            self.dmx_values[LASER_CHANNELS['color']] = self.color_list[self.color_index]
            self.color_index = (self.color_index + 1) % len(self.color_list)
        if 'position' in self.sh_sync_modes:
            self.dmx_values[SPIDER_HEAD_CHANNELS['leftTilt']] = random.randint(0, 255)
            self.dmx_values[SPIDER_HEAD_CHANNELS['rightTilt']] = random.randint(0, 255)
        if 'color' in self.sh_sync_modes:
            if self.sh_color_index == 0:
                self.set_sh_color('red')
            elif self.sh_color_index == 1:
                self.set_sh_color('green')
            elif self.sh_color_index == 2:
                self.set_sh_color('blue')
            elif self.sh_color_index == 3:
                self.set_sh_color('white')
            self.sh_color_index = (self.sh_color_index + 1) % 4
        self.send_request()

    def start_sending_dmx(self):
        """Démarre l'envoi de données DMX selon le tempo."""
        if not self.laser_sync_modes and not self.included_lights_strobe and not self.sh_sync_modes:
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
        self.laser_vertical_adjust = value
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
                if 'movingHead' in self.included_lights_breathe:
                    self.included_lights_breathe.remove('movingHead')
            self.dmx_values[MOVING_HEAD_CHANNELS['mode']] = MOVING_HEAD_MODES.get(mode, next(iter(MOVING_HEAD_MODES.values())))
        elif light == 'spiderHead':
            if mode == 'blackout':
                self.dmx_values[SPIDER_HEAD_CHANNELS['mode']] = 0
                self.dmx_values[SPIDER_HEAD_CHANNELS['brightness']] = 0
            elif mode == 'manual':
                self.dmx_values[SPIDER_HEAD_CHANNELS['on/off']] = ON
                self.dmx_values[SPIDER_HEAD_CHANNELS['strobe']] = ON # Needs to be at 255 for stable light (weird)
                self.dmx_values[SPIDER_HEAD_CHANNELS['mode']] = SPIDER_HEAD_MODES.get(mode, next(iter(SPIDER_HEAD_MODES.values())))
            else:
                self.dmx_values[SPIDER_HEAD_CHANNELS['mode']] = SPIDER_HEAD_MODES.get(mode, next(iter(SPIDER_HEAD_MODES.values())))
        elif light == 'strobe':
            self.rf_controller.set_strobe_mode(mode)
        self.send_request()

    def set_laser_pattern(self, pattern):
        """Définit le pattern."""
        default_pattern = next(iter(LASER_PATTERNS.values()))
        self.dmx_values[LASER_CHANNELS['pattern']] = LASER_PATTERNS.get(pattern, default_pattern)
        self.send_request()
        
    def set_mh_gobo(self, gobo):
        """Définit le gobo du Moving Head."""
        self.dmx_values[MOVING_HEAD_CHANNELS['gobo']] = MOVING_HEAD_GOBOS.get(gobo, next(iter(MOVING_HEAD_GOBOS.values())))
        self.send_request()
        
    def set_mh_scene_gobo_switch(self, isOn):
        """Active ou désactive le gobo du Moving Head."""
        self.mh_scene_gobo_switch = isOn
    
    def set_color(self, color, light):
        """Définit la couleur."""
        if light == 'laser':
            print("Changing laser color: ", color)
            self.set_laser_color(color)
        elif light == 'movingHead':
            print("Changing moving head color: ", color)
            self.set_mh_color(color)
        elif light == 'spiderHead':
            self.set_sh_color(color)
        elif light == 'strobe':
            self.rf_controller.set_strobe_color(color)
        elif light == 'all':
            print("Changing all laser and moving head color: ", color)
            self.set_laser_color(color)
            self.set_mh_color(color)
        self.send_request()
        
    def set_sh_led_selection(self, leds: List[LEDCell]):
        """
        Définit les LEDs à activer pour le Spider Head.
        """
        for led in leds:
            if led.side == 'left':
                self.dmx_values[SPIDER_HEAD_CHANNELS[led.color + 'L']] = SPIDER_HEAD_COLOR_ON if led.isOn else SPIDER_HEAD_COLOR_OFF
            elif led.side == 'right':
                self.dmx_values[SPIDER_HEAD_CHANNELS[led.color + 'R']] = SPIDER_HEAD_COLOR_ON if led.isOn else SPIDER_HEAD_COLOR_OFF
        self.send_request()
        
    def set_sh_strobe_speed(self, speed):
        """
        Définit la vitesse du stroboscope pour le Spider Head.
        - Paramètre 'speed' : entre 0 (minimum) et 100 (maximum).
        - Valeur DMX de 16 à 131.
        """
        # 1) Borne le speed entre 0 et 100
        speed = max(0, min(speed, 100))
        
        if speed == 0:
            self.dmx_values[SPIDER_HEAD_CHANNELS['strobe']] = ON
            self.send_request()
            return

        # 2) Convertit en valeur DMX (16..131)
        DMX_MIN = 16
        DMX_MAX = 131
        dmx_range = DMX_MAX - DMX_MIN  # 131 - 16 = 115

        # Interpolation linéaire
        # speed=0   => DMX_MIN
        # speed=100 => DMX_MAX
        dmx_value = DMX_MIN + int(dmx_range * (speed / 100.0))

        # 3) Met à jour la valeur DMX
        self.dmx_values[SPIDER_HEAD_CHANNELS['strobe']] = dmx_value

        # 4) Envoie la mise à jour
        self.send_request()
        
    def set_sh_chase_speed(self, speed):
        """
        Définit la vitesse du chase pour le Spider Head.
        - Paramètre 'speed' : entre 0 (arrêt) et 100 (maximum).
        """
        if speed == 0.0:
            if self._chase_thread and self._chase_thread.is_alive():
                self._chase_stop_event.set()   # signale l'arrêt au thread
                self._chase_thread.join()      # attend la fin
            self._chase_thread = None
            self._current_speed = 0.0
            # Coupe le stroboscope
            print("[Chase] Stopped (speed=0).")
        else:
            # => Mettre à jour la vitesse
            self._current_speed = speed
            print(f"[Chase] Speed set to {self._current_speed}")

            # Si un thread est déjà en cours, on ne le recrée pas
            if self._chase_thread and self._chase_thread.is_alive():
                print("[Chase] Thread already running, updated speed only.")
                return

            # Sinon, on crée un event stop et on lance la boucle
            self._chase_stop_event = Event()
            self._chase_thread = Thread(target=self._chase_loop)
            self._chase_thread.start()
            print("[Chase] New thread started.")
        
    def set_master_strobe_chase(self, speed: float):
        """
        Lance ou met à jour la boucle 'chase' en fonction de 'speed' (0..100).
        
        - speed == 0 : arrête le chase, coupe le strobe.
        - speed != 0 :
            * si un thread existe déjà => on met juste à jour self._current_speed
            * sinon => on crée un thread pour exécuter _chase_loop()
        """
        # 1) Bornage de speed
        speed = max(0.0, min(speed, 100.0))

        if speed == 0.0:
            self.set_mh_strobe_speed(0)
            self.set_sh_strobe_speed(0)
            # => Arrêter la boucle s'il y en a une
            if self._chase_thread and self._chase_thread.is_alive():
                self._chase_stop_event.set()   # signale l'arrêt au thread
                self._chase_thread.join()      # attend la fin
            self._chase_thread = None
            self._current_speed = 0.0
            # Coupe le stroboscope
            print("[Chase] Stopped (speed=0).")
        else:
            # => Mettre à jour la vitesse
            self._current_speed = speed
            mh_speed = max(5, speed - 10)
            self.set_mh_strobe_speed(mh_speed)
            self.set_sh_strobe_speed(speed)
            self.rf_controller.adjust_strobe_speed(speed)
            print(f"[Chase] Speed set to {self._current_speed}")

            # Si un thread est déjà en cours, on ne le recrée pas
            if self._chase_thread and self._chase_thread.is_alive():
                print("[Chase] Thread already running, updated speed only.")
                return

            # Sinon, on crée un event stop et on lance la boucle
            self._chase_stop_event = Event()
            self._chase_thread = Thread(target=self._chase_loop)
            self._chase_thread.start()
            print("[Chase] New thread started.")
    
    # -----------------------------------------------------------------------
    # Boucle interne, exécutée dans le thread
    # -----------------------------------------------------------------------
    def _chase_loop(self):
        """
        Boucle “infinie” (tant qu'on ne reçoit pas l'event stop)
        qui active le stroboscope, puis effectue un cycle R->G->B->W à gauche
        et W->B->G->R à droite, en boucle, lisant self._current_speed à chaque itération.
        """
        # Active stroboscope
        print("[Chase] Loop running...")

        left_colors = ["red", "green", "blue", "white"]
        right_colors = ["white", "blue", "green", "red"]

        # Boucle tant que l'event “stop” n'est pas déclenché
        while not self._chase_stop_event.is_set():
            # Parcourt les 4 "lignes"
            for i in range(4):
                if self._chase_stop_event.is_set():
                    break  # sort immédiatement si on a demandé l'arrêt

                # Allume la couleur i à gauche
                self.set_sh_color(left_colors[i], side="left")
                # Allume la couleur i à droite (inverse)
                self.set_sh_color(right_colors[i], side="right")

                # Délai : ex. plus speed est grand, plus la pause est petite
                delay = self._compute_delay(self._current_speed)
                time.sleep(delay)

                # Blink off
                self.set_sh_color("off", side="both")
                time.sleep(delay * 0.2)

        # En sortant de la boucle => strobe off
        print("[Chase] Loop ended.")
    
    # -----------------------------------------------------------------------
    # Méthodes auxiliaires
    # -----------------------------------------------------------------------
    def _compute_delay(self, speed: float) -> float:
        """
        Ex.: plus speed est grand, plus c'est rapide => on dort moins longtemps.
        speed=1   => delay ~ 1s
        speed=100 => delay ~ 0.01s
        Ajuste la formule selon le ressenti souhaité.
        """
        if speed <= 1:
            return 2.0
        else:
            return 2.0 / speed
        

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
            self.dmx_values[LASER_CHANNELS['vertical movement']] = self.laser_vertical_adjust
        self.send_request()

    def send_request(self, force=False):
        if self.pause_dmx_send and not force:
            return
        dmx_values_str = ','.join(map(str, self.dmx_values))
        url = f'http://{self.olad_ip}:{self.olad_port}/set_dmx'
        payload = {'u': self.universe, 'd': dmx_values_str}
        try:
            response = requests.post(url, data=payload, timeout=5)  # Timeout de 5 secondes
            print("DMX values sent")
            return response
        except requests.exceptions.RequestException as e:
            print(f"Error sending DMX request: {e}")

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
            self.mh_scene = scene
        elif scene == 'medium':
            self.dmx_values[MOVING_HEAD_CHANNELS['pan running']] = 0
            self.dmx_values[MOVING_HEAD_CHANNELS['tilt running']] = 0
            self.dmx_values[MOVING_HEAD_CHANNELS['auto mode']] = MOVING_HEAD_AUTO['panTilt']
            self.dmx_values[MOVING_HEAD_CHANNELS['running speed']] = MOVING_HEAD_MEDIUM_RUNNING
            if self.mh_scene_gobo_switch:
                self.dmx_values[MOVING_HEAD_CHANNELS['gobo']] = MOVING_HEAD_MEDIUM_GOBO
            self.mh_scene = scene
        elif scene == 'fast':
            self.dmx_values[MOVING_HEAD_CHANNELS['pan running']] = 0
            self.dmx_values[MOVING_HEAD_CHANNELS['tilt running']] = 0
            self.dmx_values[MOVING_HEAD_CHANNELS['auto mode']] = MOVING_HEAD_AUTO['panTilt']
            self.dmx_values[MOVING_HEAD_CHANNELS['running speed']] = MOVING_HEAD_FAST_RUNNING
            if self.mh_scene_gobo_switch:
                self.dmx_values[MOVING_HEAD_CHANNELS['gobo']] = MOVING_HEAD_FAST_GOBO
            self.mh_scene = scene
        elif scene == 'off':
            self.dmx_values[MOVING_HEAD_CHANNELS['pan running']] = 0
            self.dmx_values[MOVING_HEAD_CHANNELS['tilt running']] = 0
            self.dmx_values[MOVING_HEAD_CHANNELS['auto mode']] = 0
            self.dmx_values[MOVING_HEAD_CHANNELS['running speed']] = 0
            if self.mh_scene_gobo_switch:
                self.dmx_values[MOVING_HEAD_CHANNELS['gobo']] = 0
            self.mh_scene = scene
        self.send_request()
        
    def set_sh_scene(self, scene):
        """
        Définit la scène du Spider Head (slow, medium, fast).
        """
        print("Setting scene to: ", scene)
        self.sh_scene = scene
        self.should_play_sh_scene = False
        
        if scene == 'off':
            self.dmx_values[SPIDER_HEAD_CHANNELS["speed"]] = 0
            self.dmx_values[SPIDER_HEAD_CHANNELS["leftTilt"]] = 0
            self.dmx_values[SPIDER_HEAD_CHANNELS["rightTilt"]] = 0
            self.send_request()
            return
        else:
            self.sh_position = None

        # Récupérer la vitesse DMX pour la scène
        speed = SPIDER_HEAD_SCENE_SPEED.get(scene, SPIDER_HEAD_SCENE_SPEED["slow"])
        
        # Reset la position
        self.dmx_values[SPIDER_HEAD_CHANNELS["speed"]] = 0 # Max speed
        self.dmx_values[SPIDER_HEAD_CHANNELS["leftTilt"]] = 0
        self.dmx_values[SPIDER_HEAD_CHANNELS["rightTilt"]] = 0
        self.send_request(force=True)
        
        time.sleep(0.2)  # Attendre un peu avant de démarrer la scène
        
        # Configurer la vitesse de rotation
        self.dmx_values[SPIDER_HEAD_CHANNELS["speed"]] = speed

        # Démarrer la scène
        self.run_scene(scene)

    def run_scene(self, scene):
        """
        Lance l'effet de rotation des faisceaux selon la scène définie.
        """
        if hasattr(self, "scene_thread") and self.scene_thread.is_alive():
            # Si une scène est déjà en cours, arrêter proprement le thread
            self.should_play_sh_scene = False
            self.scene_thread.join()

        self.should_play_sh_scene = True

        # Déterminer la durée totale d'une rotation complète
        scene_durations = {
            "slow": 9.8,  # 10 secondes pour slow
            "medium": 2.8,  # 2,88 secondes pour medium
            "fast": 0.76,  # 0,96 secondes pour fast
        }
        rotation_time = scene_durations.get(scene, 10.0)

        def scene_logic():
            # Boucle pour alterner les positions DMX
            while self.should_play_sh_scene:
                # Gauche
                self.dmx_values[SPIDER_HEAD_CHANNELS["leftTilt"]] = 255
                self.dmx_values[SPIDER_HEAD_CHANNELS["rightTilt"]] = 255
                self.send_request()

                # Pause pour la moitié du temps de rotation (avec interruptions)
                self._interruptible_sleep(rotation_time)

                if not self.should_play_sh_scene:
                    break  # Quitter la boucle si une nouvelle scène est demandée

                # Droite
                self.dmx_values[SPIDER_HEAD_CHANNELS["leftTilt"]] = 0
                self.dmx_values[SPIDER_HEAD_CHANNELS["rightTilt"]] = 0
                self.send_request()

                # Pause pour la moitié du temps de rotation (avec interruptions)
                self._interruptible_sleep(rotation_time)

        # Créer un thread pour exécuter la logique en arrière-plan
        self.scene_thread = Thread(target=scene_logic, daemon=True)
        self.scene_thread.start()


    def _interruptible_sleep(self, duration):
        """
        Interrompt le sommeil si la scène change avant la fin du délai.
        """
        interval = 0.1  # Vérifie toutes les 100 ms
        elapsed = 0
        while elapsed < duration:
            if not self.should_play_sh_scene:
                break  # Quitter si une nouvelle scène est demandée
            time.sleep(interval)
            elapsed += interval

    def set_mh_brightness(self, dimmer):
        """Définit le dimmer du Moving Head."""
        value = int((dimmer / 100.0) * 255)
        if value == 0 and 'movingHead' in self.included_lights_breathe:
            self.included_lights_breathe.remove('movingHead')
        print("Setting dimmer to ", value)
        self.dmx_values[MOVING_HEAD_CHANNELS['dimming']] = value
        self.send_request()
        
    def set_sh_brightness(self, dimmer):
        """Définit le dimmer du Spider Head."""
        value = int((dimmer / 100.0) * 255)
        self.dmx_values[SPIDER_HEAD_CHANNELS['brightness']] = value
        self.send_request()
        
    def set_breathe_mode(self, included_lights):
        """Définit le mode de respiration du Moving Head."""
        self.included_lights_breathe = included_lights
        self.trigger_breathing()
        
    def set_breathe_mode_cue(self, light, included_lights):
        if light in included_lights and light not in self.included_lights_breathe:
            self.included_lights_breathe.append(light)
        elif light not in included_lights and light in self.included_lights_breathe:
            self.included_lights_breathe.remove(light)
        self.trigger_breathing()
            
    def trigger_breathing(self):
        """Démarre l'effet de respiration."""
        if self.included_lights_breathe:
                # Vérifie si un thread précédent existe et est terminé
                if hasattr(self, "breathe_thread") and self.breathe_thread.is_alive():
                    return
                # Crée un nouveau thread pour le mode breathe
                self.breathe_thread = Thread(target=self.breathe, daemon=True)
                self.breathe_thread.start()
        else:
            # Assure que le thread actuel s'arrête proprement
            if hasattr(self, "breathe_thread") and self.breathe_thread.is_alive():
                self.breathe_thread.join()  # Attends que le thread se termine
            print("Effet de respiration arrêté")

    def breathe(self):
        if not self.included_lights_breathe:
            return

        # Temps de référence pour le premier cycle
        reference_time = time.time()

        while self.included_lights_breathe:
            # Calcul de la durée totale du cycle en secondes
            full_cycle = (60.0 / self.current_tempo) * self.multiplier  # Temps pour un cycle complet (BPM ajusté)
            half_cycle = full_cycle / 2  # Temps pour la moitié du cycle (fade-in ou fade-out)

            # Étape 1 : Augmentation instantanée ou fade-in progressif
            if self.slow_breathe:
                # Fade-in progressif
                start_time = time.time()

                while time.time() - start_time <= half_cycle:
                    if not self.included_lights_breathe:
                        return  # Arrêt immédiat si demandé

                    # Calcul du temps écoulé depuis le début du fade-in
                    elapsed_time = time.time() - start_time

                    # Augmentation progressive
                    current_intensity = int(255 * (elapsed_time / half_cycle))

                    # Applique l'intensité calculée
                    for light in self.included_lights_breathe:
                        if light == 'movingHead':
                            self.dmx_values[MOVING_HEAD_CHANNELS['dimming']] = current_intensity
                        elif light == 'spiderHead':
                            self.dmx_values[SPIDER_HEAD_CHANNELS['brightness']] = current_intensity
                    self.send_request()
            else:
                # Augmentation instantanée
                for light in self.included_lights_breathe:
                    if light == 'movingHead':
                        self.dmx_values[MOVING_HEAD_CHANNELS['dimming']] = 255
                    elif light == 'spiderHead':
                        self.dmx_values[SPIDER_HEAD_CHANNELS['brightness']] = 255
                self.send_request()

            # Étape 2 : Fade-out progressif (immédiatement après dans le cas instantané)
            start_time = time.time()
            
            fade_out_time = half_cycle if self.slow_breathe else full_cycle

            while time.time() - start_time <= fade_out_time:
                if not self.included_lights_breathe:
                    return  # Arrêt immédiat si demandé

                # Calcul du temps écoulé depuis le début du fade-out
                elapsed_time = time.time() - start_time

                # Calcul linéaire de la luminosité décroissante
                current_intensity = int(255 * (1 - (elapsed_time / fade_out_time)))

                # Applique l'intensité calculée
                for light in self.included_lights_breathe:
                    if light == 'movingHead':
                        self.dmx_values[MOVING_HEAD_CHANNELS['dimming']] = current_intensity
                    elif light == 'spiderHead':
                        self.dmx_values[SPIDER_HEAD_CHANNELS['brightness']] = current_intensity
                self.send_request()

            # Recalibrage du temps pour le prochain cycle
            reference_time += full_cycle
            time_to_next_cycle = reference_time - time.time()

            # Attends exactement le temps restant avant le prochain cycle
            if time_to_next_cycle > 0:
                time.sleep(time_to_next_cycle)

    def set_mh_strobe_speed(self, value):
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
        
    def set_sh_color(self, color, side = 'both'):
        """Définit la couleur du Spider Head."""
        if color == 'red':
            if side == 'both' or side == 'left':
                # Left
                self.dmx_values[SPIDER_HEAD_CHANNELS['redL']] = SPIDER_HEAD_COLOR_ON
                self.dmx_values[SPIDER_HEAD_CHANNELS['greenL']] = SPIDER_HEAD_COLOR_OFF
                self.dmx_values[SPIDER_HEAD_CHANNELS['blueL']] = SPIDER_HEAD_COLOR_OFF
                self.dmx_values[SPIDER_HEAD_CHANNELS['whiteL']] = SPIDER_HEAD_COLOR_OFF
            if side == 'both' or side == 'right':
                self.dmx_values[SPIDER_HEAD_CHANNELS['redR']] = SPIDER_HEAD_COLOR_ON
                self.dmx_values[SPIDER_HEAD_CHANNELS['greenR']] = SPIDER_HEAD_COLOR_OFF
                self.dmx_values[SPIDER_HEAD_CHANNELS['blueR']] = SPIDER_HEAD_COLOR_OFF
                self.dmx_values[SPIDER_HEAD_CHANNELS['whiteR']] = SPIDER_HEAD_COLOR_OFF
        elif color == 'green':
            if side == 'both' or side == 'left':
                # Left
                self.dmx_values[SPIDER_HEAD_CHANNELS['redL']] = SPIDER_HEAD_COLOR_OFF
                self.dmx_values[SPIDER_HEAD_CHANNELS['greenL']] = SPIDER_HEAD_COLOR_ON
                self.dmx_values[SPIDER_HEAD_CHANNELS['blueL']] = SPIDER_HEAD_COLOR_OFF
                self.dmx_values[SPIDER_HEAD_CHANNELS['whiteL']] = SPIDER_HEAD_COLOR_OFF
            if side == 'both' or side == 'right':
                # Right
                self.dmx_values[SPIDER_HEAD_CHANNELS['redR']] = SPIDER_HEAD_COLOR_OFF
                self.dmx_values[SPIDER_HEAD_CHANNELS['greenR']] = SPIDER_HEAD_COLOR_ON
                self.dmx_values[SPIDER_HEAD_CHANNELS['blueR']] = SPIDER_HEAD_COLOR_OFF
                self.dmx_values[SPIDER_HEAD_CHANNELS['whiteR']] = SPIDER_HEAD_COLOR_OFF
        elif color == 'blue':
            if side == 'both' or side == 'left':
                # Left
                self.dmx_values[SPIDER_HEAD_CHANNELS['redL']] = SPIDER_HEAD_COLOR_OFF
                self.dmx_values[SPIDER_HEAD_CHANNELS['greenL']] = SPIDER_HEAD_COLOR_OFF
                self.dmx_values[SPIDER_HEAD_CHANNELS['blueL']] = SPIDER_HEAD_COLOR_ON
                self.dmx_values[SPIDER_HEAD_CHANNELS['whiteL']] = SPIDER_HEAD_COLOR_OFF
            if side == 'both' or side == 'right':
                # Right
                self.dmx_values[SPIDER_HEAD_CHANNELS['redR']] = SPIDER_HEAD_COLOR_OFF
                self.dmx_values[SPIDER_HEAD_CHANNELS['greenR']] = SPIDER_HEAD_COLOR_OFF
                self.dmx_values[SPIDER_HEAD_CHANNELS['blueR']] = SPIDER_HEAD_COLOR_ON
                self.dmx_values[SPIDER_HEAD_CHANNELS['whiteR']] = SPIDER_HEAD_COLOR_OFF
        elif color == 'white':
            if side == 'both' or side == 'left':
                # Left
                self.dmx_values[SPIDER_HEAD_CHANNELS['redL']] = SPIDER_HEAD_COLOR_OFF
                self.dmx_values[SPIDER_HEAD_CHANNELS['greenL']] = SPIDER_HEAD_COLOR_OFF
                self.dmx_values[SPIDER_HEAD_CHANNELS['blueL']] = SPIDER_HEAD_COLOR_OFF
                self.dmx_values[SPIDER_HEAD_CHANNELS['whiteL']] = SPIDER_HEAD_COLOR_ON
            if side == 'both' or side == 'right':
                # Right
                self.dmx_values[SPIDER_HEAD_CHANNELS['redR']] = SPIDER_HEAD_COLOR_OFF
                self.dmx_values[SPIDER_HEAD_CHANNELS['greenR']] = SPIDER_HEAD_COLOR_OFF
                self.dmx_values[SPIDER_HEAD_CHANNELS['blueR']] = SPIDER_HEAD_COLOR_OFF
                self.dmx_values[SPIDER_HEAD_CHANNELS['whiteR']] = SPIDER_HEAD_COLOR_ON
        elif color == 'multicolor':
            if side == 'both' or side == 'left':
                # Left
                self.dmx_values[SPIDER_HEAD_CHANNELS['redL']] = SPIDER_HEAD_COLOR_ON
                self.dmx_values[SPIDER_HEAD_CHANNELS['greenL']] = SPIDER_HEAD_COLOR_ON
                self.dmx_values[SPIDER_HEAD_CHANNELS['blueL']] = SPIDER_HEAD_COLOR_ON
                self.dmx_values[SPIDER_HEAD_CHANNELS['whiteL']] = SPIDER_HEAD_COLOR_ON
            if side == 'both' or side == 'right':
                # Right
                self.dmx_values[SPIDER_HEAD_CHANNELS['redR']] = SPIDER_HEAD_COLOR_ON
                self.dmx_values[SPIDER_HEAD_CHANNELS['greenR']] = SPIDER_HEAD_COLOR_ON
                self.dmx_values[SPIDER_HEAD_CHANNELS['blueR']] = SPIDER_HEAD_COLOR_ON
                self.dmx_values[SPIDER_HEAD_CHANNELS['whiteR']] = SPIDER_HEAD_COLOR_ON
        self.send_request()
        
    def set_mh_pan_tilt(self, pan, tilt):
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
        
    def set_sh_position(self, leftAngle, rightAngle):
        """
        Définit la position des faisceaux pour le Spider Head.
        """
        self.should_play_sh_scene = False
        self.sh_scene = 'off'
        leftAngle = int((leftAngle / 180) * 255)
        rightAngle = int((rightAngle / 180) * 255)
        self.sh_position = {"leftAngle": leftAngle, "rightAngle": rightAngle}
        self.dmx_values[SPIDER_HEAD_CHANNELS["speed"]] = 0
        self.dmx_values[SPIDER_HEAD_CHANNELS["leftTilt"]] = leftAngle
        self.dmx_values[SPIDER_HEAD_CHANNELS["rightTilt"]] = rightAngle
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
        if cue.type == "temporary":
            self.backup_state(cue.affectedLights)
        self.pause_dmx_send = True
        
        if cue.changeBpmMultiplier:
            self.multiplier = cue.bpmMultiplier
        if cue.changeBreatheMode:
            if cue.breatheMode == "slow":
                self.slow_breathe = True
            elif cue.breatheMode == "fast":
                self.slow_breathe = False

        # Appliquer les réglages pour le Laser
        if "laser" in cue.affectedLights:
            self.set_mode_for("laser", cue.laser.mode)

            for setting in cue.laserSettings:
                if setting == "color":
                    self.set_laser_color(cue.laser.color)
                    if "color" in cue.laser.bpmSyncModes and "color" not in self.laser_sync_modes:
                        self.add_sync_mode("color")
                    elif "color" not in cue.laser.bpmSyncModes and "color" in self.laser_sync_modes:
                        self.remove_sync_mode("color")
                elif setting == "pattern":
                    self.set_laser_pattern(cue.laser.pattern)
                    self.set_laser_pattern_include(list(cue.laser.includedPatterns))
                    if "pattern" in cue.laser.bpmSyncModes and "pattern" not in self.laser_sync_modes:
                        self.add_sync_mode("pattern")
                    elif "pattern" not in cue.laser.bpmSyncModes and "pattern" in self.laser_sync_modes:
                        self.remove_sync_mode("pattern")
                elif setting == "hAnimation":
                    self.set_horizontal_animation(cue.laser.horizontalAnimationEnabled, cue.laser.horizontalAnimationSpeed)
                elif setting == "vAnimation":
                    self.set_vertical_animation(cue.laser.verticalAnimationEnabled, cue.laser.verticalAnimationSpeed)
                elif setting == "vAdjust":
                    self.set_vertical_adjust(cue.laser.verticalAdjust)
                elif setting == "strobe":
                    self.set_strobe_mode_cue("laser", cue.includedLightsStrobe)

        # Appliquer les réglages pour les Moving Heads
        if "movingHead" in cue.affectedLights:
            self.set_mode_for("movingHead", cue.movingHead.mode)

            for setting in cue.movingHeadSettings:
                if setting == "color":
                    self.set_mh_color(cue.movingHead.color, cue.movingHead.colorSpeed)
                elif setting == "scene":
                    self.set_mh_scene(cue.movingHead.scene)
                elif setting == "strobeSpeed":
                    self.set_mh_strobe_speed(cue.movingHead.strobeSpeed)
                elif setting == "brightness":
                    self.set_mh_brightness(cue.movingHead.brightness)
                    self.set_breathe_mode_cue("movingHead", cue.includedLightsBreathe)
                elif setting == "position" and cue.movingHead.positionPreset:
                    print("Setting position preset to:", cue.movingHead.positionPreset)
                    self.set_mh_pan_tilt(
                        cue.movingHead.positionPreset["pan"],
                        cue.movingHead.positionPreset["tilt"]
                    )
                elif setting == "strobe":
                    self.set_strobe_mode_cue("movingHead", cue.includedLightsStrobe)
                elif setting == "gobo":
                    self.set_mh_gobo(cue.movingHead.gobo)
                        
        if "spiderHead" in cue.affectedLights:
            self.set_mode_for("spiderHead", cue.spiderHead.mode)
            
            for setting in cue.spiderHeadSettings:
                if setting == "color":
                    if cue.spiderHead.ledSelection:
                        leds = cue.spiderHead.ledSelection
                        self.set_sh_led_selection(leds)
                    else:
                        self.set_sh_color(cue.spiderHead.color)
                elif setting == "chaseSpeed":
                    self.set_sh_chase_speed(cue.spiderHead.chaseSpeed)
                elif setting == "brightness":
                    self.set_sh_brightness(cue.spiderHead.brightness)
                    self.set_breathe_mode_cue("spiderHead", cue.includedLightsBreathe)
                elif setting == "scene":
                    self.set_sh_scene(cue.spiderHead.scene)
                elif setting == "strobeSpeed":
                    self.set_sh_strobe_speed(cue.spiderHead.strobeSpeed)
                elif setting == "position":
                    self.set_sh_position(cue.spiderHead.position['leftAngle'], cue.spiderHead.position['rightAngle'])

        self.pause_dmx_send = False
        self.send_request()
        
    def backup_state(self, affected_lights):
        self.backup = StateBackup(self)
        print("Creating backup, included lights breathe:", self.included_lights_breathe)
        backup_variables = BackupVariables(
            self.laser_sync_modes.copy(),
            self.sh_sync_modes.copy(),
            self.included_lights_strobe.copy(),
            self.included_lights_breathe.copy(),
            self.laser_pattern_include.copy(),
            self.should_play_sh_scene,
            self.laser_vertical_adjust,
            self.sh_scene,
            self.sh_position,
            self._current_speed,
            self.multiplier,
            self.slow_breathe
        )
        self.backup.backup_state(self.dmx_values, backup_variables, affected_lights)
        
    def set_dmx_values_for(self, affected_lights, dmx_values):
        """
        Définit les valeurs DMX à envoyer.
        """
        if 'laser' in affected_lights:
            self.dmx_values[:9] = dmx_values[:9].copy()
        if 'movingHead' in affected_lights:
            self.dmx_values[20:32] = dmx_values[20:32].copy()
        if 'spiderHead' in affected_lights:
            self.dmx_values[40:55] = dmx_values[40:55].copy()
        self.send_request()
        
    def restore_state(self):
        """
        Restaure l'état précédent.
        """
        self.backup.restore_state()