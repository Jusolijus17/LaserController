import broadlink
from rf_signals import *

class RFController:
    def __init__(self):
        self.device = None
        self.is_strobe_on = False
        self.is_strobe_reset = True
        self.current_strobe_level = 0
            
    def setup(self):
        devices = self.discover_devices()
        if len(devices) != 0:
            self.authenticate(devices)
            
    def discover_devices(self):
        print("Discovering devices...")
        devices = broadlink.discover()
        print(devices)
        if len(devices) == 0:
            connect = input("No devices found. Would you like to connect to a Wi-Fi network? (y/n): ")
            if connect == 'y':
                self.connect_to_wifi()
            return
        else:
            for device in devices:
                self.authenticate(device)
            return devices
            
    def connect_to_wifi(self):
        print("Long press the reset button until the blue LED is blinking quickly.")
        print("Long press again until blue LED is blinking slowly.")
        print("Manually connect to the WiFi SSID named BroadlinkProv.")
        ssid = input('Enter the SSID of the Wi-Fi network: ')
        password = input('Enter the password of the Wi-Fi network: ')
        broadlink.setup(ssid, password, 3)
        self.discover_devices()
        
    def authenticate(self, devices):
        # Si `devices` n'est pas une liste, le convertir en liste
        if not isinstance(devices, list):
            devices = [devices]

        for device in devices:
            print(device)
            if "RM4 pro" in device.model:
                authenticated = device.auth()
                if authenticated:
                    print("Successfully authenticated with device:", device.model)
                    self.device = device
                else:
                    print("Failed to authenticate with device:", device.model)
                break
            
    def send_rf_signal(self, signal):
        if self.device is None:
            print("No device found. Please setup the device.")
            return
        self.device.send_data(signal)
        
    def turn_on_strobe(self):
        self.is_strobe_on = True
        self.send_rf_signal(STROBE_ON)
        
    def turn_off_strobe(self):
        self.is_strobe_on = False
        self.send_rf_signal(STROBE_OFF)
        
    def set_strobe_on_off(self, is_on):
        if is_on:
            self.turn_on_strobe()
        else:
            self.turn_off_strobe()
        
    def set_strobe_mode(self, mode):
        if mode == 'auto':
            self.send_rf_signal(STROBE_AUTO)
        elif mode == 'mic' or mode == 'sound':
            self.send_rf_signal(STROBE_MIC)
            
    def set_strobe_color(self, color):
        if color == 'red':
            self.send_rf_signal(STROBE_RED)
        elif color == 'green':
            self.send_rf_signal(STROBE_GREEN)
        elif color == 'blue':
            self.send_rf_signal(STROBE_BLUE)
        elif color == 'white':
            self.send_rf_signal(STROBE_WHITE)
        elif color == 'yellow':
            self.send_rf_signal(STROBE_YELLOW)
        elif color == 'pink':
            self.send_rf_signal(STROBE_PINK)
        elif color == 'blue':
            self.send_rf_signal(STROBE_BLUE)
        elif color == 'purple':
            self.send_rf_signal(STROBE_PURPLE)
        elif color == 'multicolor':
            self.send_rf_signal(STROBE_MULTICOLOR)
            
    def strobe_faster(self):
        self.send_rf_signal(STROBE_AUTO_PLUS)
        self.is_strobe_reset = False
        
    def strobe_slower(self):
        self.send_rf_signal(STROBE_AUTO_MINUS)
        
    def adjust_strobe_speed(self, speed):
        if speed < 40:
            self.reset_strobe_speed()
            return
        # Calcul du niveau cible (proportionnel à la vitesse)
        target_strobe_level = (speed - 40) // 4  # Chaque step de 3 = 1 niveau
        target_strobe_level = min(target_strobe_level, 15)

        # Monter graduellement : ajuster d'un seul niveau à la fois
        if target_strobe_level > self.current_strobe_level:
            print(f"Increasing strobe: {self.current_strobe_level} -> {self.current_strobe_level + 1}")
            self.current_strobe_level += 1
            if not self.is_strobe_on:
                self.turn_on_strobe()
            self.strobe_faster()
        elif target_strobe_level < self.current_strobe_level:
            print(f"Decreasing strobe: {self.current_strobe_level} -> {self.current_strobe_level - 1}")
            self.current_strobe_level -= 1
            self.strobe_slower()
        else:
            print("Strobe level unchanged")
        
    def reset_strobe_speed(self, force=False):
        if not self.is_strobe_reset or force:
            if force:
                self.turn_on_strobe()
            self.is_strobe_reset = True
            for i in range(15):
                self.send_rf_signal(STROBE_AUTO_MINUS)
            self.turn_off_strobe()
            
    def strobe_max_speed(self):
        self.turn_on_strobe()
        self.set_strobe_mode('auto')
        self.set_strobe_color('multicolor')
        for i in range(15):
            self.send_rf_signal(STROBE_AUTO_PLUS)
        self.is_strobe_reset = False
        
    def smoke_on(self):
        self.send_rf_signal(SMOKE_ON)
        
    def smoke_off(self):
        self.send_rf_signal(SMOKE_OFF)
        
    def set_smoke_on_off(self, is_on):
        if is_on:
            self.smoke_on()
        else:
            self.smoke_off()
        
if __name__ == "__main__":
    controller = RFController()