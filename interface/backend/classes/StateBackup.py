from dataclasses import dataclass

@dataclass
class BackupVariables:
    laser_sync_modes: set
    sh_sync_modes: set
    included_lights_strobe: set
    included_lights_breathe: set
    laser_pattern_include: list
    should_play_sh_scene: bool
    laser_vertical_adjust: int
    sh_scene: str
    sh_position: dict
    current_speed: int
    bpm_multiplier: float
    slow_breathe: bool

class StateBackup:
    def __init__(self, dmx_controller):
        self.dmx_controller = dmx_controller
        self.variables: BackupVariables
        self.dmx_values = [0] * 512
        self.affected_lights = set()
        
    def backup_state(self, dmx_values, variables: BackupVariables, affected_lights):
        self.backup_dmx_values(dmx_values)
        self.backup_variables(variables)
        self.affected_lights = affected_lights.copy()
        print("State backed up")

    def backup_dmx_values(self, values):
        self.dmx_values = values.copy()
        print("DMX values backed up: ", self.dmx_values)
        
    def backup_variables(self, variables: BackupVariables):
        self.variables = variables
        
    def restore_state(self):
        self.restore_dmx_values()
        self.restore_variables()
        self.restore_loops()
        print("State restored")
        
    def restore_dmx_values(self):
        self.dmx_controller.set_dmx_values_for(self.affected_lights, self.dmx_values)
        
    def restore_variables(self):
        if 'laser' in self.affected_lights:
            self.dmx_controller.laser_sync_modes = self.variables.laser_sync_modes.copy()
            self.dmx_controller.laser_vertical_adjust = self.variables.laser_vertical_adjust
            self.dmx_controller.laser_pattern_include = self.variables.laser_pattern_include.copy()
        if 'spiderHead' in self.affected_lights:
            self.dmx_controller.sh_position = self.variables.sh_position
            self.dmx_controller.sh_scene = self.variables.sh_scene
            self.dmx_controller.sh_sync_modes = self.variables.sh_sync_modes.copy()
            self.dmx_controller.should_play_sh_scene = self.variables.should_play_sh_scene
            
        self.dmx_controller.included_lights_strobe = self.variables.included_lights_strobe.copy()
        self.dmx_controller.included_lights_breathe = self.variables.included_lights_breathe.copy()
        self.dmx_controller.bpm_multiplier = self.variables.bpm_multiplier
        self.dmx_controller.slow_breathe = self.variables.slow_breathe
        
    def restore_loops(self):
        self.dmx_controller.start_sending_dmx()
        self.dmx_controller.trigger_breathing()
        if 'spiderHead' in self.affected_lights:
            if self.variables.should_play_sh_scene:
                print("Restoring SH scene")
                self.dmx_controller.set_sh_scene(self.variables.sh_scene)
            elif self.variables.sh_position:
                print("Restoring SH position")
                self.dmx_controller.set_sh_position(self.variables.sh_position)
            self.dmx_controller.set_sh_chase_speed(self.variables.current_speed)