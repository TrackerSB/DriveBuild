from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Optional


class AIMode(Enum):
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
    mode: Optional[AIMode] = None
    speed_limit: Optional[float] = None
    target_speed: Optional[float] = None


@dataclass
class InitialState:
    position: Tuple[float, float]
    orientation: float
    mode: AIMode
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


@dataclass
class ScenarioMapping:
    from dataclasses import field
    from lxml.etree import _ElementTree
    environment: _ElementTree
    filename: str
    crit_defs: List[_ElementTree] = field(default_factory=list)


@dataclass
class TestCase:
    from generator import ScenarioBuilder
    from kp_transformer import Criteria
    scenario: ScenarioBuilder
    crit_def: Criteria
    authors: List[str]
