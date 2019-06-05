from typing import List, Tuple, Optional

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
        from beamngpy import ProceduralCone, ProceduralCube, ProceduralCylinder
        from dbtypes.scheme import Cone, Cube, Cylinder
        from util import eprint
        for obstacle in self.obstacles:
            obstacle_type = type(obstacle)
            height = obstacle.height
            pos = (obstacle.x, obstacle.y, height / 2.0)
            rot = (obstacle.x_rot, obstacle.y_rot, obstacle.z_rot)
            name = obstacle.oid
            if obstacle_type is Cube:
                mesh = ProceduralCube(pos, rot, (obstacle.length, obstacle.width, height), name=name)
            elif obstacle_type is Cylinder:
                mesh = ProceduralCylinder(pos, rot, obstacle.radius, height=height, name=name)
            elif obstacle_type is Cone:
                mesh = ProceduralCone(pos, rot, obstacle.base_radius, height, name=name)
            else:
                eprint("Obstacles of type " + str(obstacle_type) + " are not supported by the generation, yet.")
                mesh = None
            if mesh:
                scenario.add_procedural_mesh(mesh)

    def add_participants_to_scenario(self, scenario: Scenario) -> None:
        from dbtypes.beamng import DBVehicle
        for participant in self.participants:
            # FIXME Adjust color
            vehicle = DBVehicle(participant.id, model=participant.model, color="White", licence=participant.id)
            for request in participant.ai_requests:
                vehicle.apply_request(request)
            initial_state = participant.initial_state
            scenario.add_vehicle(vehicle,
                                 pos=(initial_state.position[0], initial_state.position[1], 0),
                                 rot=(0, 0, -initial_state.orientation))

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
    from util.xml import xpath, get_tag_name
    from util import eprint
    from requests import PositionRequest, SpeedRequest, SteeringAngleRequest, CameraRequest, CameraDirection, \
        LidarRequest

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
        ai_requests = list()
        request_nodes = xpath(node, "db:ai/*")
        for req_node in request_nodes:
            tag = get_tag_name(req_node)
            rid = req_node.get("id")
            if tag == "position":
                ai_requests.append(PositionRequest(rid))
            elif tag == "speed":
                ai_requests.append(SpeedRequest(rid))
            elif tag == "steeringAngle":
                ai_requests.append(SteeringAngleRequest(rid))
            elif tag == "camera":
                width = int(req_node.get("width"))
                height = int(req_node.get("height"))
                fov = int(req_node.get("fov"))
                direction = CameraDirection[req_node.get("direction")]
                ai_requests.append(CameraRequest(rid, width, height, fov, direction))
            elif tag == "lidar":
                radius = int(req_node.get("radius"))
                ai_requests.append(LidarRequest(rid, radius))
            else:
                eprint("The tag " + tag + " is not supported, yet.")
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
        participants.append(Participant(id, initial_state, CarModel[node.get("model")].value, movements, ai_requests))
    return ScenarioBuilder(lanes, obstacles, participants)
