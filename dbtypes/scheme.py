from dataclasses import dataclass
from enum import Enum
from typing import Tuple, Optional, List


class MovementMode(Enum):
    MANUAL = "manual"
    AUTONOMOUS = "autonomous"
    TRAINING = "training"


class CarModel(Enum):
    ETK800 = "etk800"


class CarLight(Enum):
    LOW_BEAM = "lowBeam",
    HIGH_BEAM = "highBeam",
    SIGNAL_L = "signalL",
    SIGNAL_R = "signalR",
    SIGNAL_WARN = "signalWarn",
    FOG_LIGHTS = "fogLights"


Position = Tuple[float, float]


@dataclass
class WayPoint:
    position: Position
    tolerance: float
    id: Optional[str] = None
    mode: Optional[MovementMode] = None
    speed_limit: Optional[float] = None
    target_speed: Optional[float] = None


@dataclass
class InitialState:
    position: Tuple[float, float]
    orientation: float
    mode: MovementMode
    speed_limit: Optional[float] = None
    target_speed: Optional[float] = None


@dataclass
class Obstacle:
    positions: List[Position]
    height: float


@dataclass
class Participant:
    id: str
    initial_state: InitialState
    model: CarModel
    movement: List[WayPoint]


@dataclass
class LaneNode:
    position: Position
    width: float


@dataclass
class Lane:
    nodes: List[LaneNode]
    id: Optional[str] = None


@dataclass
class ScenarioMapping:
    from dataclasses import field
    from lxml.etree import _ElementTree
    environment: _ElementTree
    filename: str
    crit_defs: List[_ElementTree] = field(default_factory=list)
