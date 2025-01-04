from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class LEDCell:
    id: int
    color: str
    side: str
    isOn: bool

    @classmethod
    def from_dict(cls, data: Dict) -> "LEDCell":
        color_value = data.get("color", "red")
        if isinstance(color_value, dict):
            color_value = color_value.get("name", "red")

        return cls(
            id=data.get("id", 0),
            color=color_value,
            side=data.get("side", "left"),
            isOn=data.get("isOn", False)
        )

@dataclass
class SpiderHeadState:
    color: str = "multicolor"
    ledSelection: Optional[List[LEDCell]] = None
    mode: str = "blackout"
    scene: str = "off"
    chaseSpeed: float = 0.0
    brightness: float = 0.0
    strobeSpeed: float = 0.0

    def to_dict(self) -> Dict:
        """Convertit l'état de SpiderHead en dictionnaire."""
        return {
            "color": self.color,
            "ledSelection": [led.to_dict() for led in self.ledSelection] if self.ledSelection else None,
            "mode": self.mode,
            "scene": self.scene,
            "chaseSpeed": self.chaseSpeed,
            "brightness": self.brightness,
            "strobeSpeed": self.strobeSpeed,
        }

    @staticmethod
    def from_dict(data: Dict) -> "SpiderHeadState":
        """Recrée un SpiderHeadState depuis un dictionnaire."""
        return SpiderHeadState(
            color=data.get("color", "red"),
            ledSelection=[LEDCell.from_dict(led) for led in data.get("ledSelection", [])] if data.get("ledSelection") else None,
            mode=data.get("mode", "blackout"),
            scene=data.get("scene", "off"),
            chaseSpeed=data.get("chaseSpeed", 0.0),
            brightness=data.get("brightness", 0.0),
            strobeSpeed=data.get("strobeSpeed", 0.0),
        )