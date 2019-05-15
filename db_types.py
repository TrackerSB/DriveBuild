from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Optional

from beamngpy import Road, BeamNGpy


class MovementMode(Enum):
    MANUAL = "manual"
    AUTONOMOUS = "autonomous"
    TRAINING = "training"


class CarModel(Enum):
    ETK800 = "etk800"


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


class DBRoad(Road):
    def __init__(self, id: str, material, **options):
        super().__init__(material, **options)
        self.id = id


@dataclass
class ScenarioMapping:
    from dataclasses import field
    from lxml.etree import _ElementTree
    environment: _ElementTree
    filename: str
    crit_defs: List[_ElementTree] = field(default_factory=list)


class DBBeamNGpy(BeamNGpy):
    def __init__(self, host, port, home=None, user=None):
        super().__init__(host, port, home, user)
        self.current_tick = 0

    def step(self, count, wait=True):
        super().step(count, wait)
        self.current_tick += 1
