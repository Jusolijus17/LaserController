from tkinter import ON


LASER_COLORS = {
    "multicolor" : 62,
    "red": 65,
    "green": 96,
    "blue": 129,
    "yellow": 161,
    "pink": 193,
    "cyan": 225,
}

LASER_PATTERNS = {
    "straight": 158, # -----
    "dashed": 161, # - - -
    "dotted": 236, # . . . . . .
    "wave": 120, # /\/\/\/\/\
}

LASER_MODES = {
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

MOVING_HEAD_GOBOS = {
    0: 0,
    1: 10,
    2: 19,
    3: 28,
    4: 33,
    5: 42,
    6: 49,
    7: 56,
}

MOVING_HEAD_SLOW_RUNNING = 181
MOVING_HEAD_SLOW_COLOR = 155
MOVING_HEAD_MEDIUM_RUNNING = 126
MOVING_HEAD_MEDIUM_COLOR = 155
MOVING_HEAD_MEDIUM_GOBO = 170
MOVING_HEAD_FAST_RUNNING = 100
MOVING_HEAD_FAST_GOBO = 150

SPIDER_HEAD_CHANNELS = {
    "rightTilt": 40,
    "leftTilt": 41,
    "speed": 42,
    "brightness": 43,
    "strobe": 44,
    "redL": 45,
    "greenL": 46,
    "blueL": 47,
    "whiteL": 48,
    "redR": 49,
    "greenR": 50,
    "blueR": 51,
    "whiteR": 52,
    "mode": 53,
    "on/off": 54
}

SPIDER_HEAD_COLOR_ON = 255
SPIDER_HEAD_COLOR_OFF = 0

SPIDER_HEAD_MODES = {
    "manual": 0,
    "auto": 25,
    "sound": 100,
}

SPIDER_HEAD_SCENE_SPEED = {
    "slow": 249,
    "medium": 231,
    "fast": 199,
}

ON = 255
OFF = 0


LIGHTS = {
    "laser",
    "movingHead",
    "spiderHead"
    "all"
}