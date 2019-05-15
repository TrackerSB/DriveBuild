from abc import ABC
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple


class KPValue(Enum):
    """
    Represents the Kleene-Priest logic.
    """
    TRUE = True,
    FALSE = False,
    UNKNOWN = None

    # NOTE Do not underestimate the complexity of the implementation of these logical operators!
    def __and__(self, other):
        if self.value == self.FALSE or other.value == self.FALSE:
            return self.FALSE
        if self.value == self.UNKNOWN or other.value == self.UNKNOWN:
            return self.UNKNOWN
        return self.TRUE

    def __or__(self, other):
        if self.value == self.TRUE or other.value == self.TRUE:
            return self.TRUE
        if self.value == self.UNKNOWN or other.value == self.UNKNOWN:
            return self.UNKNOWN
        return self.FALSE

    def __neg__(self):
        if self.value == self.TRUE:
            return self.FALSE
        if self.value == self.FALSE:
            return self.TRUE
        return self.UNKNOWN


class Evaluable(ABC):
    from abc import abstractmethod
    @abstractmethod
    def eval(self) -> KPValue:
        pass


class Criteria(Evaluable, ABC):
    from beamngpy import Scenario

    def __init__(self, scenario: Scenario) -> None:
        self.scenario = scenario


# State conditions
class StateCondition(Criteria, ABC):
    from beamngpy import Scenario, Vehicle

    def __init__(self, scenario: Scenario, participant: str) -> None:
        super().__init__(scenario)
        # TODO Check existence of participant id
        self.participant = participant

    def get_participant(self) -> Vehicle:
        return self.scenario.get_vehicle(self.participant)


class SCPosition(StateCondition):
    from beamngpy import Scenario

    def __init__(self, scenario: Scenario, participant: str, x: float, y: float, tolerance: float):
        super().__init__(scenario, participant)
        if tolerance < 0:
            raise ValueError("The tolerance must be non negative.")
        self.x = x
        self.y = y
        self.tolerance = tolerance

    def eval(self) -> KPValue:
        from numpy import array
        from numpy.linalg import norm
        x, y, _ = self.get_participant().state["pos"]
        return KPValue.TRUE if norm(array((x, y)) - array((self.x, self.y))) <= self.tolerance else KPValue.FALSE


class SCArea(StateCondition):
    from beamngpy import Scenario

    def __init__(self, scenario: Scenario, participant: str, points: List[Tuple[float, float]]):
        from shapely.geometry import Polygon
        super().__init__(scenario, participant)
        self.polygon = Polygon(points)

    def eval(self) -> KPValue:
        x, y, _ = self.get_participant().state["pos"]
        return self.polygon.contains((x, y))


class SCLane(StateCondition):
    from beamngpy import Scenario

    def __init__(self, scenario: Scenario, participant: str, lane: str):
        super().__init__(scenario, participant)
        # TODO Check existence of lane id
        self.lane = lane

    def eval(self) -> KPValue:
        # FIXME Implement SCLane
        if self.lane == "offroad":
            for road in self.scenario.roads:
                pass
        else:
            for road in self.scenario.roads:
                pass
        return KPValue.UNKNOWN


class SCSpeed(StateCondition):
    from beamngpy import Scenario

    def __init__(self, scenario: Scenario, participant: str, speed_limit: float):
        super().__init__(scenario, participant)
        if speed_limit < 0:
            raise ValueError("Speed limits must be non negative.")
        self.speed_limit = speed_limit

    def eval(self) -> KPValue:
        from numpy.linalg import norm
        return KPValue.FALSE if norm(self.get_participant().state["vel"]) > self.speed_limit else KPValue.TRUE


# Validation constraints
class ValidationConstraint(Criteria, ABC):
    from abc import abstractmethod
    from beamngpy import Scenario

    def __init__(self, scenario: Scenario, inner: Evaluable) -> None:
        super().__init__(scenario)
        self.inner = inner

    def eval(self) -> KPValue:
        # FIXME How to distinguish VCs that got ignored from ones that could not be determined?
        return self.inner.eval() if self.eval_cond() == KPValue.TRUE else KPValue.UNKNOWN

    @abstractmethod
    def eval_cond(self) -> KPValue:
        pass


class VCPosition(ValidationConstraint):
    from beamngpy import Scenario

    def __init__(self, scenario: Scenario, inner: Evaluable, participant: str, x: float, y: float, tolerance: float):
        super().__init__(scenario, inner)
        self.scPosition = SCPosition(scenario, participant, x, y, tolerance)

    def eval_cond(self) -> KPValue:
        return self.scPosition.eval()


class VCArea(ValidationConstraint):
    from beamngpy import Scenario

    def __init__(self, scenario: Scenario, inner: Evaluable, participant: str, points: List[Tuple[float, float]]):
        super().__init__(scenario, inner)
        self.scArea = SCArea(scenario, participant, points)

    def eval_cond(self) -> KPValue:
        return self.scArea.eval()


class VCLane(ValidationConstraint):
    from beamngpy import Scenario

    def __init__(self, scenario: Scenario, inner: Evaluable, participant: str, lane: str):
        super().__init__(scenario, inner)
        self.scLane = SCLane(scenario, participant, lane)

    def eval_cond(self) -> KPValue:
        return self.scLane.eval()


class VCSpeed(ValidationConstraint):
    from beamngpy import Scenario

    def __init__(self, scenario: Scenario, inner: Evaluable, participant: str, speed_limit: float):
        super().__init__(scenario, inner)
        self.scSpeed = SCSpeed(scenario, participant, speed_limit)

    def eval_cond(self) -> KPValue:
        return self.scSpeed.eval()


# Connectives
class Connective(Evaluable, ABC):
    pass


class BinaryConnective(Connective, ABC):
    def __init__(self, left: Criteria, right: Criteria) -> None:
        self.left = left
        self.right = right


class And(BinaryConnective):
    def eval(self) -> KPValue:
        return self.left.eval() and self.right.eval()


class Or(BinaryConnective):
    def eval(self) -> KPValue:
        return self.left.eval() or self.right.eval()


class Not(Connective):
    def __init__(self, evaluable: Evaluable) -> None:
        self.evaluable = evaluable

    def eval(self) -> KPValue:
        return self.evaluable.eval()


# Test case type
@dataclass
class TestCase:
    from generator import ScenarioBuilder
    scenario: ScenarioBuilder
    crit_def: Evaluable
    authors: List[str]
