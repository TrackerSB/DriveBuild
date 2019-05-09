from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple


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


@dataclass
class MovementNode:
    waypoint: WayPoint
    mode: AIMode = None
    speed_limit: float = None,
    target_speed: float = None


@dataclass
class InitialState:
    position: Tuple[float, float]
    orientation: float
    mode: AIMode
    speed_limit: float = None
    target_speed: float = None


@dataclass
class Obstacle:
    positions: List[Position]
    height: float


@dataclass
class Participant:
    initial_state: InitialState
    model: CarModel
    movement: List[MovementNode]


@dataclass
class LaneNode:
    position: Position
    width: float


Lane = List[LaneNode]
