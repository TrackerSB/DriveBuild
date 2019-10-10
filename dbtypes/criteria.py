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
        """
        Evaluates to KPValue.TRUE only if the condition got triggered.
        """
        pass


class UnknownEvaluable(Evaluable):
    """
    A class that can be used for representing an "empty" evaluable e.g. representing an empty precondition criterion.
    """

    def eval(self) -> KPValue:
        return KPValue.UNKNOWN


class Criterion(Evaluable, ABC):
    def __init__(self, scenario: Scenario) -> None:
        self.scenario = scenario


# State conditions
# FIXME Recognize "any" participant
class StateCondition(Criterion, ABC):
    """
    NOTE: A StateCondition does never call Vehicle::update_vehicle() which has to be called before every evaluation.
    """
    from abc import abstractmethod
    from requests import AiRequest
    from util import static_vars
    from beamngpy import Vehicle
    from typing import Any

    def __init__(self, scenario: Scenario, participant: str) -> None:
        super().__init__(scenario)
        # TODO Check existence of participant id
        self.participant = participant
        self.requests = self._create_requests()
        for request in self.requests:
            vehicle = self._get_vehicle()
            request.add_sensor_to(vehicle)
            # Make sure vehicle sensor_cache is not empty
            if self._is_simulation_running():
                scenario.bng.poll_sensors(vehicle)

    def _get_vehicle(self) -> Vehicle:
        return self.scenario.get_vehicle(self.participant)

    def _poll_request_data(self) -> List[Any]:
        request_data = []
        for request in self.requests:
            request_data.append(request.read_sensor_cache_of(self._get_vehicle()))
        return request_data

    @static_vars(prefix="criterion_", counter=0)
    def _generate_rid(self) -> str:
        while True:  # Pseudo "do-while"-loop
            rid = StateCondition._generate_rid.prefix + str(StateCondition._generate_rid.counter)
            if rid in self._get_vehicle().sensors:
                StateCondition._generate_rid.counter += 1
            else:
                break
        return rid

    def _is_simulation_running(self) -> bool:
        return self.scenario.bng is not None

    def eval(self) -> KPValue:
        if self._is_simulation_running():
            return self._eval_impl()
        else:
            return KPValue.UNKNOWN

    @abstractmethod
    def _eval_impl(self) -> KPValue:
        pass

    @abstractmethod
    def _create_requests(self) -> List[AiRequest]:
        pass


class SCPosition(StateCondition):
    from requests import AiRequest

    def __init__(self, scenario: Scenario, participant: str, x: float, y: float, tolerance: float):
        super().__init__(scenario, participant)
        if tolerance < 0:
            raise ValueError("The tolerance must be non negative.")
        self.x = x
        self.y = y
        self.tolerance = tolerance

    def _create_requests(self) -> List[AiRequest]:
        from requests import PositionRequest
        return [PositionRequest(self._generate_rid())]

    def _eval_impl(self) -> KPValue:
        from numpy import array
        from numpy.linalg import norm
        x, y = self._poll_request_data()[0]
        return KPValue.TRUE if norm(array((x, y)) - array((self.x, self.y))) <= self.tolerance else KPValue.FALSE


class SCArea(StateCondition):
    from requests import AiRequest

    def __init__(self, scenario: Scenario, participant: str, points: List[Tuple[float, float]]):
        from shapely.geometry import Polygon
        super().__init__(scenario, participant)
        self.polygon = Polygon(points)

    def _create_requests(self) -> List[AiRequest]:
        from requests import PositionRequest
        return [PositionRequest(self._generate_rid())]

    def _eval_impl(self) -> KPValue:
        from shapely.geometry import Point
        x, y = self._poll_request_data()[0]
        return KPValue.TRUE if self.polygon.contains(Point(x, y)) else KPValue.FALSE


class SCLane(StateCondition):
    from requests import AiRequest

    def __init__(self, scenario: Scenario, participant: str, lane: str):
        super().__init__(scenario, participant)
        # TODO Check existence of lane id
        self.lane = lane

    def _create_requests(self) -> List[AiRequest]:
        from requests import BoundingBoxRequest
        return [BoundingBoxRequest(self._generate_rid())]

    def _eval_impl(self) -> KPValue:
        from typing import Dict
        from shapely.geometry import Polygon
        from drivebuildclient.common import eprint
        bbox = self._poll_request_data()[0]

        def _to_polygon(road_edges: List[Dict[str, float]]) -> Polygon:
            points = [p["left"][0:2] for p in road_edges]
            right_edge_points = [p["right"][0:2] for p in road_edges]
            right_edge_points.reverse()
            points.extend(right_edge_points)
            return Polygon(shell=points)

        if self.lane == "offroad":
            is_offroad = KPValue.TRUE
            for road in self.scenario.roads:
                if road.rid:
                    edges = self.scenario.bng.get_road_edges(road.rid)
                    polygon = _to_polygon(edges)
                    if polygon.intersects(bbox):
                        is_offroad = KPValue.FALSE
                        break
                else:
                    eprint("SCLane can not consider roads without ID.")
            return is_offroad
        else:
            for road in self.scenario.roads:
                edges = self.scenario.bng.get_road_edges(road.rid)
                polygon = _to_polygon(edges)
                return KPValue.TRUE if polygon.intersects(bbox) else KPValue.FALSE


class SCSpeed(StateCondition):
    from requests import AiRequest

    def __init__(self, scenario: Scenario, participant: str, speed_limit: float):
        super().__init__(scenario, participant)
        if speed_limit < 0:
            raise ValueError("Speed limits must be non negative.")
        self.speed_limit = speed_limit

    def _create_requests(self) -> List[AiRequest]:
        from requests import SpeedRequest
        return [SpeedRequest(self._generate_rid())]

    def _eval_impl(self) -> KPValue:
        return KPValue.TRUE if self._poll_request_data()[0] > self.speed_limit else KPValue.FALSE


class SCDamage(StateCondition):
    from requests import AiRequest

    def __init__(self, scenario: Scenario, participant: str):
        super().__init__(scenario, participant)

    def _create_requests(self) -> List[AiRequest]:
        from requests import DamageRequest
        return [DamageRequest(self._generate_rid())]

    def _eval_impl(self) -> KPValue:
        return KPValue.TRUE if self._poll_request_data()[0] else KPValue.FALSE


class SCDistance(StateCondition):
    from requests import AiRequest

    def __init__(self, scenario: Scenario, participant: str, other_participant: str, max_distance: float):
        super().__init__(scenario, participant)
        if max_distance < 0:
            raise ValueError("The maximum allowed distance has to be non negative.")
        # TODO Check whether other_participant id exists
        self.other_participant = other_participant
        self.max_distance = max_distance

    def _create_requests(self) -> List[AiRequest]:
        from requests import PositionRequest
        return [PositionRequest(self._generate_rid())]

    def _eval_impl(self) -> KPValue:
        from numpy import array
        from numpy.linalg import norm
        x1, y1 = self._poll_request_data()[0]
        # FIXME This circumvents the request mechanism...
        x2, y2, _ = self.scenario.get_vehicle(self.other_participant)["pos"]
        return KPValue.FALSE if norm(array((x1, y1)) - array((x2, y2))) > self.max_distance else KPValue.TRUE


class SCLight(StateCondition):
    from dbtypes.scheme import CarLight
    from requests import AiRequest

    def __init__(self, scenario: Scenario, participant: str, light: CarLight):
        super().__init__(scenario, participant)
        self.light = light

    def _create_requests(self) -> List[AiRequest]:
        from requests import LightRequest
        return [LightRequest(self._generate_rid())]

    def _eval_impl(self) -> KPValue:
        # FIXME Implement light criterion
        print(self._poll_request_data()[0])
        return KPValue.UNKNOWN


class SCWaypoint(StateCondition):
    from requests import AiRequest

    def __init__(self, scenario: Scenario, participant: str, waypoint: str):
        super().__init__(scenario, participant)
        # TODO Check whether waypoint id exists
        self.waypoint = waypoint

    def _create_requests(self) -> List[AiRequest]:
        return []

    def _eval_impl(self) -> KPValue:
        # FIXME Implement waypoint criterion
        return KPValue.UNKNOWN


# Validation constraints
class ValidationConstraint(Criterion, ABC):
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
        from dbtypes.beamngpy import DBBeamNGpy
        from warnings import warn
        bng = self.scenario.bng
        if bng and type(bng) is DBBeamNGpy:
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
        return KPValue.TRUE if all(map(lambda e: e.eval() is KPValue.TRUE, self.evaluables)) else KPValue.FALSE


class Or(BinaryConnective):
    def eval(self) -> KPValue:
        return KPValue.TRUE if any(map(lambda e: e.eval() is KPValue.TRUE, self.evaluables)) else KPValue.FALSE


class Not(Connective):
    def __init__(self, evaluable: Evaluable) -> None:
        self.evaluable = evaluable

    def eval(self) -> KPValue:
        return not self.evaluable.eval()  # FIXME How to force usage of custom not?


CriteriaFunction = Callable[[Scenario], Evaluable]


# Test case type
@dataclass
class TestCase:
    from generator import ScenarioBuilder
    name: str
    scenario: ScenarioBuilder
    precondition_fct: CriteriaFunction
    success_fct: CriteriaFunction
    failure_fct: CriteriaFunction
    stepsPerSecond: int
    aiFrequency: int
    authors: List[str]
