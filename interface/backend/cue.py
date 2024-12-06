from dataclasses import dataclass, field
from typing import List, Set, Optional, Dict
from uuid import UUID, uuid4


@dataclass
class Color:
    red: float
    green: float
    blue: float
    opacity: float

    def to_dict(self) -> Dict[str, float]:
        """Convert the Color object to a dictionary."""
        return {
            "red": self.red,
            "green": self.green,
            "blue": self.blue,
            "opacity": self.opacity,
        }

    @staticmethod
    def from_dict(data: Dict[str, float]) -> "Color":
        """Create a Color object from a dictionary."""
        return Color(
            red=data.get("red", 0.0),
            green=data.get("green", 0.0),
            blue=data.get("blue", 0.0),
            opacity=data.get("opacity", 1.0),
        )


@dataclass
class Cue:
    id: UUID = field(default_factory=uuid4)
    color: Color = Color(1.0, 0.0, 0.0, 1.0)  # Default to red with full opacity
    name: str = ""

    # Laser
    includeLaser: bool = False
    laserColor: str = ""
    laserBPMSyncModes: List[str] = field(default_factory=list)
    laserMode: str = "blackout"
    laserPattern: str = "straight"
    laserIncludedPatterns: Set[str] = field(default_factory=lambda: {"straight", "dashed", "dotted", "wave"})

    # Moving Head
    includeMovingHead: bool = False
    movingHeadMode: str = "blackout"
    movingHeadColor: str = ""
    movingHeadColorFrequency: float = 0.0
    movingHeadStrobeFrequency: float = 0.0
    movingHeadScene: str = "off"
    movingHeadBrightness: float = 50.0
    positionPreset: Optional[dict] = None

    def to_dict(self) -> Dict:
        """Serialize the Cue object to a dictionary."""
        return {
            "id": str(self.id),
            "color": self.color.to_dict(),
            "name": self.name,
            "includeLaser": self.includeLaser,
            "laserColor": self.laserColor,
            "laserBPMSyncModes": self.laserBPMSyncModes,
            "laserMode": self.laserMode,
            "laserPattern": self.laserPattern,
            "laserIncludedPatterns": list(self.laserIncludedPatterns),
            "includeMovingHead": self.includeMovingHead,
            "movingHeadMode": self.movingHeadMode,
            "movingHeadColor": self.movingHeadColor,
            "movingHeadColorFrequency": self.movingHeadColorFrequency,
            "movingHeadStrobeFrequency": self.movingHeadStrobeFrequency,
            "movingHeadScene": self.movingHeadScene,
            "movingHeadBrightness": self.movingHeadBrightness,
            "positionPreset": self.positionPreset,
        }

    @staticmethod
    def from_dict(data: Dict) -> "Cue":
        """Deserialize a dictionary to a Cue object."""
        return Cue(
            id=UUID(data.get("id", str(uuid4()))),
            color=Color.from_dict(data.get("color", {})),
            name=data.get("name", ""),
            includeLaser=data.get("includeLaser", False),
            laserColor=data.get("laserColor", ""),
            laserBPMSyncModes=data.get("laserBPMSyncModes", []),
            laserMode=data.get("laserMode", "blackout"),
            laserPattern=data.get("laserPattern", "straight"),
            laserIncludedPatterns=set(data.get("laserIncludedPatterns", {"straight", "dashed", "dotted", "wave"})),
            includeMovingHead=data.get("includeMovingHead", False),
            movingHeadMode=data.get("movingHeadMode", "blackout"),
            movingHeadColor=data.get("movingHeadColor", ""),
            movingHeadColorFrequency=data.get("movingHeadColorFrequency", 0.0),
            movingHeadStrobeFrequency=data.get("movingHeadStrobeFrequency", 0.0),
            movingHeadScene=data.get("movingHeadScene", "off"),
            movingHeadBrightness=data.get("movingHeadBrightness", 50.0),
            positionPreset=data.get("positionPreset"),
        )