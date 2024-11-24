from re import M


COLORS = {
    "multicolor" : 62,
    "red": 65,
    "green": 96,
    "blue": 129,
    "yellow": 161,
    "pink": 193,
    "cyan": 225,
}

PATTERNS = {
    "pattern1": 158, # -----
    "pattern2": 161, # - - -
    "pattern3": 236, # . . . . . .
    "pattern4": 120, # /\/\/\/\/\
}

MODES = {
    "blackout": 0,
    "sound": 169,
    "auto": 67,
    "manual": 255,
}

LASER_CHANNELS = {
    "mode": 0,
    "pattern": 1,
    "zoom": 2,
    "x-axis rotation": 3,
    "y-axis rotation": 4,
    "z-axis rotation": 5,
    "horizontal movement": 6,
    "vertical movement": 7,
    "color": 8
}

MOVING_HEAD_CHANNELS = {
    "pan running": 20,
    "pan fine": 21,
    "tilt running": 22,
    "tilt fine": 23,
    "color": 24,
    "gobo": 25,
    "strobe": 26,
    "dimming": 27,
    "running speed": 28,
    "mode": 29,
    "auto mode": 30,
    "on/off": 31,
}

MOVING_HEAD_MODES = {
    "blackout": 0,
    "manual": 20,
    "auto": 120,
    "sound": 220,
}

MOVING_HEAD_COLORS = {
    "auto": 140,
    "red": 15,
    "green": 42,
    "blue": 51,
    "yellow": 33,
    "pink": 63,
    "cyan": 76,
    "orange": 24,
    "white": 0,
}

MOVING_HEAD_AUTO = {
    "pan": 15,
    "tilt": 110,
    "panTilt": 230,
    "reset": 255,
}

MOVING_HEAD_SLOW_RUNNING = 181
MOVING_HEAD_SLOW_COLOR = 155
MOVING_HEAD_MEDIUM_RUNNING = 126
MOVING_HEAD_MEDIUM_COLOR = 155
MOVING_HEAD_MEDIUM_GOBO = 170
MOVING_HEAD_FAST_RUNNING = 100
MOVING_HEAD_FAST_GOBO = 150


LIGHTS = {
    "laser",
    "movingHead",
    "both"
}