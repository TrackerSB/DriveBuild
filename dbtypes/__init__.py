from enum import Enum


class AIStatus(Enum):
    READY = "READY"
    WAITING = "WAITING"
    REQUESTED = "REQUESTED"


class AIAccessPoint:
    def __init__(self, address: str, vid: str) -> None:
        self.address = address
        self.vid = vid
        self.status = AIStatus.READY

    def __eq__(self, other) -> bool:
        if isinstance(other, AIAccessPoint):
            return self.vid == other.vid
        return False

    def __hash__(self):
        return hash(self.vid)
