from enum import Enum


class AIStatus(Enum):
    READY = "READY"
    WAITING = "WAITING"
    REQUESTED = "REQUESTED"
