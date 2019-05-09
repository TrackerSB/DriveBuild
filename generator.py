from typing import List

from beamngpy import Scenario, Road
from lxml.etree import ElementTree

from types import Lane, Obstacle, Participant


class ScenarioBuilder:
    def __init__(self, lanes: List[Lane], obstacles: List[Obstacle], participants: List[Participant]):
        self.lanes = lanes
        self.obstacles = obstacles
        self.participants = participants

    def add_lanes_to_scenario(self, scenario: Scenario):
        for lane in self.lanes:
            road = Road('track_editor_C_center')  # FIXME Maybe change road material
            road.nodes.extend([(lp.position[0], lp.position[1], lp.width) for lp in lane])
            scenario.add_road(road)

    def add_obstacles_to_scenario(self, scenario: Scenario):
        for obstacle in self.obstacles:
            pass  # FIXME Not implemented yet

    def add_participants_to_scenario(self, scenario: Scenario):
        for participant in self.participants:
            pass  # FIXME Not implemented yet

    def add_all(self, scenario: Scenario):
        self.add_lanes_to_scenario(scenario)
        self.add_obstacles_to_scenario(scenario)
        self.add_participants_to_scenario(scenario)


def generate_scenario(env: ElementTree) -> ScenarioBuilder:
    pass
