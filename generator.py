from typing import List, Tuple, Optional

from beamngpy.sensors import Damage, Electrics
from lxml.etree import _ElementTree, _Element


class ScenarioBuilder:
    from beamngpy import Scenario
    from dbtypes.scheme import Lane, Obstacle, Participant

    def __init__(self, lanes: List[Lane], obstacles: List[Obstacle], participants: List[Participant]):
        if participants is None:
            participants = list()
        self.lanes = lanes
        self.obstacles = obstacles
        self.participants = participants

    def add_lanes_to_scenario(self, scenario: Scenario) -> None:
        from beamngpy import Road
        from dbtypes.beamng import DBRoad
        for lane in self.lanes:
            if lane.id is None:
                road = Road('a_asphalt_01_a')
            else:
                road = DBRoad('a_asphalt_01_a', lane.id)
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
            # FIXME Always add all possibly needed sensors?
            vehicle.attach_sensor("damage", Damage())
            vehicle.attach_sensor("electrics", Electrics())
            initial_state = participant.initial_state
            scenario.add_vehicle(vehicle,
                                 pos=(initial_state.position[0], initial_state.position[1], 0),
                                 rot=(0, 0, initial_state.orientation))

    def add_waypoints_to_scenario(self, scenario: Scenario) -> None:
        from util import add_to_prefab_file
        for participant in self.participants:
            wp_prefix = "wp_" + participant.id + "_"
            counter = 0
            for waypoint in participant.movement:
                if waypoint.id is None:
                    waypoint.id = wp_prefix + str(counter)
                    counter += 1
                tolerance = str(waypoint.tolerance)
                add_to_prefab_file([
                    "new BeamNGWaypoint(" + waypoint.id + "){",
                    "   drawDebug = \"0\";",
                    "   directionalWaypoint = \"0\";",  # FIXME Should I use directional waypoints?
                    "   position = \"" + str(waypoint.position[0]) + " " + str(waypoint.position[1]) + " 0\";",
                    "   scale = \"" + tolerance + " " + tolerance + " " + tolerance + "\";",
                    "   rotationMatrix = \"1 0 0 0 1 0 0 0 1\";",
                    "   mode = \"Ignore\";",  # FIXME Which mode is suitable?
                    "   canSave = \"1\";",  # FIXME Think about it
                    "   canSaveDynamicFields = \"1\";",  # FIXME Think about it
                    "};"
                ])

    def add_all(self, scenario: Scenario) -> None:
        self.add_lanes_to_scenario(scenario)
        self.add_obstacles_to_scenario(scenario)
        self.add_participants_to_scenario(scenario)
        # FIXME As long as manually inserting text it can only be called after make
        # self.add_waypoints_to_scenario(scenario)


def generate_scenario(env: _ElementTree, participants_node: _Element) -> ScenarioBuilder:
    from lxml.etree import _Element
    from dbtypes.scheme import LaneNode, Lane, Participant, InitialState, MovementMode, CarModel, WayPoint, Cube, \
        Cylinder, Cone
    from util.xml import xpath

    lanes = list()
    lane_nodes = xpath(env, "db:lanes/db:lane")
    for node in lane_nodes:
        lane_segment_nodes = xpath(node, "db:laneSegment")
        lane = Lane(list(
            map(
                lambda n: LaneNode((float(n.get("x")), float(n.get("y"))), float(n.get("width"))),
                lane_segment_nodes
            )
        ), node.get("db:id"))
        lanes.append(lane)

    # FIXME Implement generation of obstacles
    def get_obstacle_common(node: _Element) -> Tuple[float, float, float, float, float, float, Optional[str]]:
        """
        Returns the attributes all types of obstacles have in common.
        :param node: The obstacle node
        :return: x, y, x_rot, y_rot, z_rot, height, id
        """
        return float(node.get("x")), float(node.get("y")), float(node.get("x_rot", 0)), float(node.get("y_rot", 0)), \
               float(node.get("z_rot", 0)), float(node.get("height")), node.get("id", None)

    obstacles = list()
    cube_nodes = xpath(env, "db:obstacles/db:cube")
    for node in cube_nodes:
        x, y, x_rot, y_rot, z_rot, height, id = get_obstacle_common(node)
        width = float(node.get("width"))
        length = float(node.get("length"))
        obstacles.append(Cube(x, y, height, width, length, id, x_rot, y_rot, z_rot))

    cylinder_nodes = xpath(env, "db:obstacles/db:cylinder")
    for node in cylinder_nodes:
        x, y, x_rot, y_rot, z_rot, height, id = get_obstacle_common(node)
        radius = float(node.get("radius"))
        obstacles.append(Cylinder(x, y, height, radius, id, x_rot, y_rot, z_rot))

    cylinder_nodes = xpath(env, "db:obstacles/db:cone")
    for node in cylinder_nodes:
        x, y, x_rot, y_rot, z_rot, height, id = get_obstacle_common(node)
        base_radius = float(node.get("baseRadius"))
        obstacles.append(Cone(x, y, height, base_radius, id, x_rot, y_rot, z_rot))

    participants = list()
    participant_nodes = xpath(participants_node, "db:participant")
    for node in participant_nodes:
        id = node.get("id")
        initial_state_node = xpath(node, "db:initialState")[0]
        speed_limit = initial_state_node.get("speedLimit")
        target_speed = initial_state_node.get("speed")
        initial_state = InitialState(
            (float(initial_state_node.get("x")), float(initial_state_node.get("y"))),
            float(initial_state_node.get("orientation")),
            MovementMode[initial_state_node.get("movementMode")],
            None if speed_limit is None else float(speed_limit),
            None if target_speed is None else float(target_speed)
        )
        movements = list()
        waypoint_nodes = xpath(node, "db:movement/db:waypoint")
        for wp_node in waypoint_nodes:
            speed_limit = wp_node.get("speedLimit")
            target_speed = wp_node.get("speed")
            movements.append(WayPoint(
                (float(wp_node.get("x")), float(wp_node.get("y"))),
                float(wp_node.get("tolerance")),
                wp_node.get("id"),
                MovementMode[wp_node.get("movementMode")],
                None if speed_limit is None else float(speed_limit),
                None if target_speed is None else float(target_speed)
            ))
        participants.append(Participant(id, initial_state, CarModel[node.get("model")].value, movements))
    return ScenarioBuilder(lanes, obstacles, participants)
