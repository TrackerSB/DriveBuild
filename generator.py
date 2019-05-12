import re
from typing import List, Optional, Tuple

from lxml.etree import _ElementTree, _Element

from common import static_vars
from db_types import Position


@static_vars(pattern=re.compile(r"\(-?\d+,-?\d+\)(;\(-?\d+,-?\d+\))*"))
def is_valid_shape_string(pos_str: str) -> bool:
    """
    Checks whether the given string is of the form "(x_1,y_1);(x_2,y_2);...;(x_n,y_n)".
    :return: True only if the given string is of the right form.
    """
    return is_valid_shape_string.pattern.match(pos_str)


def string_to_shape(shape_string: str) -> Optional[List[Position]]:
    """
    Converts strings like "(x_1,y_1);(x_2,y_2);...;(x_n,y_n)" to a list of positions.
    :return: The list of positions represented by the given string
    """
    if is_valid_shape_string(shape_string):
        positions = list()
        position_strings = shape_string.split(";")
        for pos_str in position_strings:
            vals = pos_str.split(",")
            x_val = vals[0][1:]
            y_val = vals[1][:-1]
            positions.append((int(x_val), int(y_val)))
        return positions
    else:
        return None


class ScenarioBuilder:
    from beamngpy import Scenario
    from db_types import Lane, Obstacle, Participant

    def __init__(self, lanes: List[Lane], obstacles: List[Obstacle], participants: List[Participant]):
        if participants is None:
            participants = list()
        self.lanes = lanes
        self.obstacles = obstacles
        self.participants = participants

    def add_lanes_to_scenario(self, scenario: Scenario) -> None:
        from beamngpy import Road
        for lane in self.lanes:
            road = Road('a_asphalt_01_a')  # FIXME Maybe change road material
            road_nodes = [(lp.position[0], lp.position[1], 0, lp.width) for lp in lane.nodes]
            road.nodes.extend(road_nodes)
            scenario.add_road(road)

    def add_obstacles_to_scenario(self, scenario: Scenario) -> None:
        for obstacle in self.obstacles:
            pass  # FIXME Not implemented yet

    def add_participants_to_scenario(self, scenario: Scenario) -> None:
        from beamngpy import Vehicle
        for participant in self.participants:
            # FIXME Adjust color
            vehicle = Vehicle(participant.id, model=participant.model, color="White", licence=participant.id)
            initial_state = participant.initial_state
            scenario.add_vehicle(vehicle,
                                 pos=(initial_state.position[0], initial_state.position[1], 0),
                                 rot=(0, 0, initial_state.orientation))

    def add_all(self, scenario: Scenario) -> None:
        self.add_lanes_to_scenario(scenario)
        self.add_obstacles_to_scenario(scenario)
        self.add_participants_to_scenario(scenario)


def generate_scenario(env: _ElementTree, participants_node: _Element) -> ScenarioBuilder:
    from lxml.etree import _Element
    from db_types import LaneNode, Lane, Obstacle, Participant, InitialState, AIMode, CarModel, WayPoint
    from xml_util import xpath

    def get_point(node: _Element) -> Tuple[float, float]:
        return float(node.get("x")), float(node.get("y"))

    def node_to_lane(node: _Element) -> LaneNode:
        return LaneNode(get_point(node), float(node.get("width")))

    lanes = list()
    lane_nodes = xpath(env, "db:lanes/db:lane")
    for node in lane_nodes:
        lane_segment_nodes = xpath(node, "db:laneSegment")
        lane = Lane(list(map(node_to_lane, lane_segment_nodes)))
        lanes.append(lane)

    obstacles = list()
    obstacle_nodes = xpath(env, "db:obstacles/db:obstacle")
    for node in obstacle_nodes:
        points = string_to_shape(node.get("shape"))
        obstacles.append(Obstacle(points, node.get("height")))

    participants = list()
    participant_nodes = xpath(participants_node, "db:participant")
    for node in participant_nodes:
        id = node.get("id")
        initial_state_node = xpath(node, "db:initialState")[0]
        speed_limit = initial_state_node.get("speedLimit")
        target_speed = initial_state_node.get("speed")
        initial_state = InitialState(
            get_point(initial_state_node),
            float(initial_state_node.get("orientation")),
            AIMode[initial_state_node.get("aiMode")],
            None if speed_limit is None else float(speed_limit),
            None if target_speed is None else float(target_speed)
        )
        movements = list()
        waypoint_nodes = xpath(node, "db:movement/db:waypoint")
        for wp_node in waypoint_nodes:
            speed_limit = wp_node.get("speedLimit")
            target_speed = wp_node.get("speed")
            movements.append(WayPoint(
                get_point(wp_node),
                float(wp_node.get("tolerance")),
                AIMode[wp_node.get("aiMode")],
                None if speed_limit is None else float(speed_limit),
                None if target_speed is None else float(target_speed)
            ))
        participants.append(Participant(id, initial_state, CarModel[node.get("model")].value, movements))
    return ScenarioBuilder(lanes, obstacles, participants)
