from typing import List, Tuple, Optional

from beamngpy import BeamNGpy
from lxml.etree import _ElementTree, _Element

from drivebuildclient.common import static_vars


class ScenarioBuilder:
    from beamngpy import Scenario
    from dbtypes.scheme import Lane, Obstacle, Participant

    def __init__(self, lanes: List[Lane], obstacles: List[Obstacle], participants: List[Participant],
                 time_of_day: Optional[float]):
        if participants is None:
            participants = list()
        self.lanes = lanes
        self.obstacles = obstacles
        self.participants = participants
        self.time_of_day = time_of_day

    @static_vars(line_width=0.3, num_nodes=100, smoothness=0)
    def add_lanes_to_scenario(self, scenario: Scenario) -> None:
        from beamngpy import Road
        from shapely.geometry import LineString
        from scipy.interpolate import splev, splprep
        from numpy.ma import arange
        from numpy import repeat

        def _interpolate_nodes(old_x_vals: List[float], old_y_vals: List[float], old_width_vals: List[float],
                               num_nodes: int) -> Tuple[List[float], List[float], List[float], List[float]]:
            k = 1 if len(old_x_vals) <= 3 else 3
            pos_tck, pos_u = splprep([old_x_vals, old_y_vals], s=self.add_lanes_to_scenario.smoothness, k=k)
            step_size = 1 / num_nodes
            unew = arange(0, 1 + step_size, step_size)
            new_x_vals, new_y_vals = splev(unew, pos_tck)
            z_vals = repeat(0.01, len(unew))
            width_tck, width_u = splprep([pos_u, old_width_vals], s=self.add_lanes_to_scenario.smoothness, k=k)
            _, new_width_vals = splev(unew, width_tck)
            return new_x_vals, new_y_vals, z_vals, new_width_vals

        for lane in self.lanes:
            old_x_vals = [node.position[0] for node in lane.nodes]
            old_y_vals = [node.position[1] for node in lane.nodes]
            old_width_vals = [node.width for node in lane.nodes]
            # FIXME Set interpolate=False for all roads?
            main_road = Road('road_rubber_sticky', rid=lane.lid)
            new_x_vals, new_y_vals, z_vals, new_width_vals \
                = _interpolate_nodes(old_x_vals, old_y_vals, old_width_vals, self.add_lanes_to_scenario.num_nodes)
            main_nodes = list(zip(new_x_vals, new_y_vals, z_vals, new_width_vals))
            main_road.nodes.extend(main_nodes)
            scenario.add_road(main_road)
            if lane.markings:
                center_line = Road('line_yellow')
                center_line.nodes.extend(
                    [(x, y, z, self.add_lanes_to_scenario.line_width) for x, y, z, _ in main_nodes])
                scenario.add_road(center_line)
                for side in ["right", "left"]:
                    side_line = Road('line_white')
                    # FIXME Recognize changing widths
                    side_line_coords = LineString(zip(new_x_vals, new_y_vals)) \
                        .parallel_offset(lane.nodes[0].width / 2 - 1.5 * self.add_lanes_to_scenario.line_width,
                                         side=side) \
                        .coords.xy
                    # NOTE The parallel LineString may have a different number of points than initially given
                    num_side_line_nodes = len(side_line_coords[0])
                    z_vals = repeat(0.01, num_side_line_nodes)
                    marking_widths = repeat(self.add_lanes_to_scenario.line_width, num_side_line_nodes)
                    side_line_nodes = zip(side_line_coords[0], side_line_coords[1], z_vals, marking_widths)
                    side_line.nodes.extend(side_line_nodes)
                    scenario.add_road(side_line)

    def add_obstacles_to_scenario(self, scenario: Scenario) -> None:
        from beamngpy import ProceduralCone, ProceduralCube, ProceduralCylinder, ProceduralBump
        from dbtypes.scheme import Cone, Cube, Cylinder, Bump
        from drivebuildclient.common import eprint
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
            elif obstacle_type is Bump:
                mesh = ProceduralBump(pos, rot, obstacle.width, obstacle.length, height, obstacle.upper_length,
                                      obstacle.upper_width)
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
                                 rot=(0, 0, -initial_state.orientation - 90))

    def add_waypoints_to_scenario(self, scenario: Scenario) -> None:
        """
        As long as manually inserting text the temporary method sim_controller.py::add_waypoints_to_scenario has to be
        used.
        used.
        """
        pass

    def set_time_of_day_to(self, instance: BeamNGpy):
        if self.time_of_day:
            instance.set_tod(self.time_of_day)

    def add_all(self, scenario: Scenario) -> None:
        # NOTE time_of_day has to be called on the BeamNG instance not on a scenario
        self.add_lanes_to_scenario(scenario)
        self.add_obstacles_to_scenario(scenario)
        self.add_participants_to_scenario(scenario)
        self.add_waypoints_to_scenario(scenario)


def generate_scenario(env: _ElementTree, participants_node: _Element) -> ScenarioBuilder:
    from lxml.etree import _Element
    from dbtypes.scheme import LaneNode, Lane, Participant, InitialState, MovementMode, CarModel, WayPoint, Cube, \
        Cylinder, Cone, Bump
    from util.xml import xpath, get_tag_name
    from drivebuildclient.common import eprint, static_vars
    from requests import PositionRequest, SpeedRequest, SteeringAngleRequest, CameraRequest, CameraDirection, \
        LidarRequest, LaneCenterDistanceRequest, CarToLaneAngleRequest, BoundingBoxRequest

    lanes: List[Lane] = list()

    @static_vars(prefix="lane_", counter=0)
    def _generate_lane_id() -> str:
        while True:  # Pseudo "do-while"-loop
            lid = _generate_lane_id.prefix + str(_generate_lane_id.counter)
            if lid in map(lambda l: l.lid, lanes):
                _generate_lane_id.counter += 1
            else:
                break
        return lid

    lane_nodes = xpath(env, "db:lanes/db:lane")
    for node in lane_nodes:
        lane_segment_nodes = xpath(node, "db:laneSegment")
        lane = Lane(list(
            map(
                lambda n: LaneNode((float(n.get("x")), float(n.get("y"))), float(n.get("width"))),
                lane_segment_nodes
            )
        ), node.get("markings", "false").lower() == "true", node.get("id", _generate_lane_id()))
        lanes.append(lane)

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
        x, y, x_rot, y_rot, z_rot, height, oid = get_obstacle_common(node)
        width = float(node.get("width"))
        length = float(node.get("length"))
        obstacles.append(Cube(x, y, height, width, length, oid, x_rot, y_rot, z_rot))

    cylinder_nodes = xpath(env, "db:obstacles/db:cylinder")
    for node in cylinder_nodes:
        x, y, x_rot, y_rot, z_rot, height, oid = get_obstacle_common(node)
        radius = float(node.get("radius"))
        obstacles.append(Cylinder(x, y, height, radius, oid, x_rot, y_rot, z_rot))

    cone_nodes = xpath(env, "db:obstacles/db:cone")
    for node in cone_nodes:
        x, y, x_rot, y_rot, z_rot, height, oid = get_obstacle_common(node)
        base_radius = float(node.get("baseRadius"))
        obstacles.append(Cone(x, y, height, base_radius, oid, x_rot, y_rot, z_rot))

    bump_nodes = xpath(env, "db:obstacles/db:bump")
    for node in bump_nodes:
        x, y, x_rot, y_rot, z_rot, height, oid = get_obstacle_common(node)
        length = float(node.get("length"))
        width = float(node.get("width"))
        upper_length = float(node.get("upperLength"))
        upper_width = float(node.get("upperWidth"))
        obstacles.append(Bump(x, y, height, width, length, upper_length, upper_width, oid, x_rot, y_rot, z_rot))

    def _extract_common_state_vals(n: _Element) -> Tuple[MovementMode, Optional[float], Optional[float]]:
        speed_limit = n.get("speedLimit")
        target_speed = n.get("speed")
        return MovementMode[n.get("movementMode")], \
               None if speed_limit is None else float(speed_limit) / 3.6, \
               None if target_speed is None else float(target_speed) / 3.6

    participants = list()
    participant_nodes = xpath(participants_node, "db:participant")
    for node in participant_nodes:
        pid = node.get("id")
        initial_state_node = xpath(node, "db:initialState")[0]
        common_state_vals = _extract_common_state_vals(initial_state_node)
        initial_state = InitialState(
            (float(initial_state_node.get("x")), float(initial_state_node.get("y"))),
            float(initial_state_node.get("orientation")),
            common_state_vals[0],
            common_state_vals[1],
            common_state_vals[2]
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
            elif tag == "laneCenterDistance":
                ai_requests.append(LaneCenterDistanceRequest(rid, lanes))
            elif tag == "carToLaneAngle":
                ai_requests.append(CarToLaneAngleRequest(rid, lanes))
            elif tag == "boundingBox":
                ai_requests.append(BoundingBoxRequest(rid))
            else:
                eprint("The tag " + tag + " is not supported, yet.")
        movements = list()
        waypoint_nodes = xpath(node, "db:movement/db:waypoint")
        for wp_node in waypoint_nodes:
            common_state_vals = _extract_common_state_vals(initial_state_node)
            movements.append(WayPoint(
                (float(wp_node.get("x")), float(wp_node.get("y"))),
                float(wp_node.get("tolerance")),
                wp_node.get("id"),
                common_state_vals[0],
                common_state_vals[1],
                common_state_vals[2]
            ))
        participants.append(Participant(pid, initial_state, CarModel[node.get("model")].value, movements, ai_requests))

    time_of_day_elements = xpath(env, "db:timeOfDay")
    time_of_day = float(time_of_day_elements[0].text) if time_of_day_elements else None

    return ScenarioBuilder(lanes, obstacles, participants, time_of_day)
