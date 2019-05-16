from abc import ABC
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Callable

from beamngpy import Scenario


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
    def __init__(self, scenario: Scenario) -> None:
        self.scenario = scenario


# State conditions
# FIXME Recognize "any" participant
class StateCondition(Criteria, ABC):
    from beamngpy import Vehicle

    def __init__(self, scenario: Scenario, participant: str) -> None:
        super().__init__(scenario)
        # TODO Check existence of participant id
        self.participant = participant

    def get_participant(self) -> Vehicle:
        return self.scenario.get_vehicle(self.participant)


class SCPosition(StateCondition):
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
    def __init__(self, scenario: Scenario, participant: str, points: List[Tuple[float, float]]):
        from shapely.geometry import Polygon
        super().__init__(scenario, participant)
        self.polygon = Polygon(points)

    def eval(self) -> KPValue:
        x, y, _ = self.get_participant().state["pos"]
        return self.polygon.contains((x, y))


class SCLane(StateCondition):
    def __init__(self, scenario: Scenario, participant: str, lane: str):
        super().__init__(scenario, participant)
        # TODO Check existence of lane id
        self.lane = lane

    def eval(self) -> KPValue:
        # FIXME Implement SCLane
        if self.lane == "offroad":
            for road in self.scenario.roads:
                edges = self.scenario.bng.get_road_edges(road)
        else:
            for road in self.scenario.roads:
                edges = self.scenario.bng.get_road_edges(road)
        return KPValue.UNKNOWN


class SCSpeed(StateCondition):
    def __init__(self, scenario: Scenario, participant: str, speed_limit: float):
        super().__init__(scenario, participant)
        if speed_limit < 0:
            raise ValueError("Speed limits must be non negative.")
        self.speed_limit = speed_limit

    def eval(self) -> KPValue:
        from numpy.linalg import norm
        return KPValue.FALSE if norm(self.get_participant().state["vel"]) > self.speed_limit else KPValue.TRUE


class SCDamage(StateCondition):
    def __init__(self, scenario: Scenario, participant: str):
        super().__init__(scenario, participant)

    def eval(self) -> KPValue:
        damage = self.scenario.bng.poll_sensors(self.get_participant())["damage"]
        print(damage)
        # FIXME Determine overall damage
        # TODO Determine whether a car is really "damaged"
        return KPValue.UNKNOWN


class SCDistance(StateCondition):
    def __init__(self, scenario: Scenario, participant: str, other_participant: str, max_distance: float):
        super().__init__(scenario, participant)
        if max_distance < 0:
            raise ValueError("The maximum allowed distance has to be non negative.")
        # TODO Check whether other_participant id exists
        self.other_participant = other_participant
        self.max_distance = max_distance

    def eval(self) -> KPValue:
        from numpy import array
        from numpy.linalg import norm
        x, y, _ = self.get_participant().state["pos"]
        other_x, other_y, _ = self.scenario.get_vehicle(self.other_participant)
        return KPValue.FALSE if norm(array((x, y)) - array((other_x, other_y))) > self.max_distance else KPValue.TRUE


class SCLight(StateCondition):
    from dbtypes.scheme import CarLight

    def __init__(self, scenario: Scenario, participant: str, light: CarLight):
        super().__init__(scenario, participant)
        self.light = light

    def eval(self) -> KPValue:
        # FIXME Implement light criterion
        print(self.scenario.bng.poll_sensors(self.get_participant())["electrics"])
        return KPValue.UNKNOWN


class SCWaypoint(StateCondition):
    def __init__(self, scenario: Scenario, participant: str, waypoint: str):
        super().__init__(scenario, participant)
        # TODO Check whether waypoint id exists
        self.waypoint = waypoint

    def eval(self) -> KPValue:
        # FIXME Implement waypoint criterion
        return KPValue.UNKNOWN


# Validation constraints
class ValidationConstraint(Criteria, ABC):
    from abc import abstractmethod

    def __init__(self, scenario: Scenario, inner: Evaluable) -> None:
        super().__init__(scenario)
        self.inner = inner

    def eval(self) -> KPValue:
        # FIXME How to distinguish VCs that got ignored from ones that could not be determined?
        return self.inner.eval() if self.eval_cond() == KPValue.TRUE else KPValue.UNKNOWN

    @abstractmethod
    def eval_cond(self) -> KPValue:
        pass


class ValidationConstraintSC(ValidationConstraint, ABC):
    def __init__(self, scenario: Scenario, inner: Evaluable, sc: StateCondition):
        super().__init__(scenario, inner)
        self.sc = sc

    def eval_cond(self) -> KPValue:
        return self.sc.eval()


class VCPosition(ValidationConstraintSC):
    def __init__(self, scenario: Scenario, inner: Evaluable, sc: SCPosition):
        super().__init__(scenario, inner, sc)


class VCArea(ValidationConstraintSC):
    def __init__(self, scenario: Scenario, inner: Evaluable, sc: SCArea):
        super().__init__(scenario, inner, sc)


class VCLane(ValidationConstraintSC):
    def __init__(self, scenario: Scenario, inner: Evaluable, sc: SCLane):
        super().__init__(scenario, inner, sc)


class VCSpeed(ValidationConstraintSC):
    def __init__(self, scenario: Scenario, inner: Evaluable, sc: SCSpeed):
        super().__init__(scenario, inner, sc)


class VCDamage(ValidationConstraintSC):
    def __init__(self, scenario: Scenario, inner: Evaluable, sc: SCDamage):
        super().__init__(scenario, inner, sc)


class VCTime(ValidationConstraint):
    def __init__(self, scenario: Scenario, inner: Evaluable, from_tick: int, to_tick: int):
        # FIXME from_step/to_step inclusive/exclusive?
        super().__init__(scenario, inner)
        self.from_tick = from_tick
        self.to_tick = to_tick

    def eval_cond(self) -> KPValue:
        from dbtypes.beamng import DBBeamNGpy
        from warnings import warn
        bng = self.scenario.bng
        if type(bng) is DBBeamNGpy:
            # FIXME from_step/to_step inclusive/exclusive?
            return KPValue.TRUE if self.from_tick <= bng.current_tick <= self.to_tick else KPValue.FALSE
        else:
            warn("The underlying BeamNGpy instance does not provide time information.")


class VCDistance(ValidationConstraintSC):
    def __init__(self, scenario: Scenario, inner: Evaluable, sc: SCDistance):
        super().__init__(scenario, inner, sc)


class VCTTC(ValidationConstraint):
    from beamngpy import Scenario

    def __init__(self, scenario: Scenario, inner: Evaluable):
        super().__init__(scenario, inner)

    def eval_cond(self) -> KPValue:
        # TODO Determine collision to which participant/obstacle
        # FIXME Position is in center of car vs crash when colliding with its bounding box
        return KPValue.UNKNOWN


class VCLight(ValidationConstraintSC):
    def __init__(self, scenario: Scenario, inner: Evaluable, sc: SCLight):
        super().__init__(scenario, inner, sc)


class VCWaypoint(ValidationConstraintSC):
    from beamngpy import Scenario

    def __init__(self, scenario: Scenario, inner: Evaluable, sc: SCWaypoint):
        super().__init__(scenario, inner, sc)


# Connectives
class Connective(Evaluable, ABC):
    pass


class BinaryConnective(Connective, ABC):
    def __init__(self, evaluables: List[Evaluable]) -> None:
        self.evaluables = evaluables


class And(BinaryConnective):
    def eval(self) -> KPValue:
        return KPValue.TRUE if all(map(lambda e: e.eval(), self.evaluables)) else KPValue.FALSE


class Or(BinaryConnective):
    def eval(self) -> KPValue:
        return KPValue.TRUE if any(map(lambda e: e.eval(), self.evaluables)) else KPValue.FALSE


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
    crit_eval: Callable[[Scenario], Evaluable]
    authors: List[str]
