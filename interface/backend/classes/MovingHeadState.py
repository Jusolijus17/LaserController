from dataclasses import dataclass, field
from typing import Dict, Optional

@dataclass
class MovingHeadState:
    color: str = "red"
    gobo: int = 0
    mode: str = "blackout"
    scene: str = "off"
    brightness: float = 0.0
    strobeSpeed: float = 0.0
    colorSpeed: float = 0.0
    positionPreset: Optional[Dict] = None  # Optionnel, représente les coordonnées Pan/Tilt

    def to_dict(self) -> Dict:
        """Convertit l'état de MovingHead en dictionnaire."""
        return {
            "color": self.color,
            "gobo": self.gobo,
            "mode": self.mode,
            "scene": self.scene,
            "brightness": self.brightness,
            "strobeSpeed": self.strobeSpeed,
            "colorSpeed": self.colorSpeed,
            "positionPreset": self.positionPreset,
        }

    @staticmethod
    def from_dict(data: Dict) -> "MovingHeadState":
        """Recrée un MovingHeadState depuis un dictionnaire."""
        return MovingHeadState(
            color=data.get("color", "red"),
            gobo=data.get("gobo", 0),
            mode=data.get("mode", "blackout"),
            scene=data.get("scene", "off"),
            brightness=data.get("brightness", 0.0),
            strobeSpeed=data.get("strobeSpeed", 0.0),
            colorSpeed=data.get("colorSpeed", 0.0),
            positionPreset=data.get("positionPreset"),  # Accepte un dictionnaire ou None
        )