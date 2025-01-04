from dataclasses import dataclass, field
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from .SpiderHeadState import SpiderHeadState
from .LaserState import LaserState
from .MovingHeadState import MovingHeadState


@dataclass
class Cue:
    id: UUID = field(default_factory=uuid4)
    color: str = "red"
    name: str = ""
    type: str = "definitive"  # Peut devenir un Enum à l'avenir
    affectedLights: List[str] = field(default_factory=list)

    laser: LaserState = field(default_factory=LaserState)
    laserSettings: List[str] = field(default_factory=list)

    movingHead: MovingHeadState = field(default_factory=MovingHeadState)
    movingHeadSettings: List[str] = field(default_factory=list)
    
    spiderHead: SpiderHeadState = field(default_factory=SpiderHeadState)
    spiderHeadSettings: List[str] = field(default_factory=list)
    
    includedLightsStrobe: List[str] = field(default_factory=list)
    includedLightsBreathe: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convertit l'objet `Cue` en dictionnaire JSON-friendly."""
        return {
            "id": str(self.id),
            "color": self.color,
            "name": self.name,
            "type": self.type,
            "affectedLights": self.affectedLights,
            "laser": self.laser.to_dict(),
            "laserSettings": self.laserSettings,
            "movingHead": self.movingHead.to_dict(),
            "movingHeadSettings": self.movingHeadSettings,
            "spiderHead": self.spiderHead.to_dict(),
            "spiderHeadSettings": self.spiderHeadSettings,
            "includedLightsStrobe": self.includedLightsStrobe,
            "includedLightsBreathe": self.includedLightsBreathe,
        }

    @staticmethod
    def from_dict(data: Dict) -> "Cue":
        """Reconstruit un objet `Cue` à partir d'un dictionnaire JSON-friendly."""
        return Cue(
            id=UUID(data.get("id", str(uuid4()))),
            color=data.get("color", "red"),
            name=data.get("name", ""),
            type=data.get("type", "definitive"),
            affectedLights=data.get("affectedLights", []),  # Utilise directement des List
            laser=LaserState.from_dict(data.get("laser", {})),
            laserSettings=data.get("laserSettings", []),  # Utilise directement des List
            movingHead=MovingHeadState.from_dict(data.get("movingHead", {})),
            movingHeadSettings=data.get("movingHeadSettings", []),  # Utilise directement des List
            spiderHead=SpiderHeadState.from_dict(data.get("spiderHead", {})),
            spiderHeadSettings=data.get("spiderHeadSettings", []),  # Utilise directement des List
            includedLightsStrobe=data.get("includedLightsStrobe", []),  # Utilise directement des List
            includedLightsBreathe=data.get("includedLightsBreathe", []),  # Utilise directement des List
        )