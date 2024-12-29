from dataclasses import dataclass, field
from typing import List, Set, Dict, Optional
from uuid import UUID, uuid4

@dataclass
class LaserState:
    color: str = "multicolor"
    pattern: str = "straight"
    mode: str = "auto"
    bpmSyncModes: List[str] = field(default_factory=list)  # Liste au lieu de Set
    includedPatterns: List[str] = field(default_factory=lambda: ["straight", "dashed", "dotted", "wave"])  # Liste au lieu de Set
    verticalAdjust: float = 63.0
    horizontalAnimationEnabled: bool = False
    horizontalAnimationSpeed: float = 140.0
    verticalAnimationEnabled: bool = False
    verticalAnimationSpeed: float = 140.0

    def to_dict(self) -> Dict:
        """Sérialisation en dictionnaire."""
        return {
            "color": self.color,
            "pattern": self.pattern,
            "mode": self.mode,
            "bpmSyncModes": self.bpmSyncModes,  # Liste
            "includedPatterns": self.includedPatterns,  # Liste
            "verticalAdjust": self.verticalAdjust,
            "horizontalAnimationEnabled": self.horizontalAnimationEnabled,
            "horizontalAnimationSpeed": self.horizontalAnimationSpeed,
            "verticalAnimationEnabled": self.verticalAnimationEnabled,
            "verticalAnimationSpeed": self.verticalAnimationSpeed,
        }

    @staticmethod
    def from_dict(data: Dict) -> "LaserState":
        """Désérialisation depuis un dictionnaire."""
        return LaserState(
            color=data.get("color", "multicolor"),
            pattern=data.get("pattern", "straight"),
            mode=data.get("mode", "auto"),
            bpmSyncModes=data.get("bpmSyncModes", []),  # Accepte une liste
            includedPatterns=data.get("includedPatterns", ["straight", "dashed", "dotted", "wave"]),  # Accepte une liste
            verticalAdjust=data.get("verticalAdjust", 63.0),
            horizontalAnimationEnabled=data.get("horizontalAnimationEnabled", False),
            horizontalAnimationSpeed=data.get("horizontalAnimationSpeed", 140.0),
            verticalAnimationEnabled=data.get("verticalAnimationEnabled", False),
            verticalAnimationSpeed=data.get("verticalAnimationSpeed", 140.0),
        )