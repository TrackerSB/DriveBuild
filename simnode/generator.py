from logging import getLogger
from typing import List, Tuple, Optional

from beamngpy import BeamNGpy
from drivebuildclient import static_vars
from lxml.etree import _ElementTree, _Element

_logger = getLogger("DriveBuild.SimNode.Generator")


class ScenarioBuilder:
    from beamngpy import Scenario
    from dbtypes.scheme import Road, Obstacle, Participant

    def __init__(self, lanes: List[Road], obstacles: List[Obstacle], participants: List[Participant],
                 time_of_day: Optional[float]):
        if participants is None:
            participants = list()
        self.roads = lanes
        self.obstacles = obstacles
        self.participants = participants
        self.time_of_day = time_of_day

    @static_vars(line_width=0.15, num_nodes=100, smoothness=0)
    def add_roads_to_scenario(self, scenario: Scenario) -> None:
        from beamngpy import Road
        from shapely.geometry import LineString
        from scipy.interpolate import splev, splprep
        from numpy.ma import arange
        from numpy import repeat, linspace
        from collections import defaultdict

        @static_vars(rounding_precision=3)
        def _interpolate_nodes(old_x_vals: List[float], old_y_vals: List[float], old_width_vals: List[float],
                               num_nodes: int) -> Tuple[List[float], List[float], List[float], List[float]]:
            assert len(old_x_vals) == len(old_y_vals) == len(old_width_vals), \
                "The lists for the interpolation must have the same length."
            k = 1 if len(old_x_vals) <= 3 else 3
            pos_tck, pos_u = splprep([old_x_vals, old_y_vals], s=self.add_roads_to_scenario.smoothness, k=k)
            step_size = 1 / num_nodes
            unew = arange(0, 1 + step_size, step_size)
            new_x_vals, new_y_vals = splev(unew, pos_tck)
            z_vals = repeat(0.01, len(unew))
            width_tck, width_u = splprep([pos_u, old_width_vals], s=self.add_roads_to_scenario.smoothness, k=k)
            _, new_width_vals = splev(unew, width_tck)
            # Reduce floating point rounding errors otherwise these may cause problems with calculating parallel_offset
            return [round(v, _interpolate_nodes.rounding_precision) for v in new_x_vals], \
                   [round(v, _interpolate_nodes.rounding_precision) for v in new_y_vals], \
                   z_vals, new_width_vals

        for road in self.roads:
            unique_nodes = []
            node_pos_tracker = defaultdict(lambda: list())
            for node in road.nodes:
                x = node.position[0]
                y = node.position[1]
                if x not in node_pos_tracker or y not in node_pos_tracker[x]:
                    unique_nodes.append(node)
                    node_pos_tracker[x].append(y)
            old_x_vals = [node.position[0] for node in unique_nodes]
            old_y_vals = [node.position[1] for node in unique_nodes]
            old_width_vals = [node.width for node in unique_nodes]
            # FIXME Set interpolate=False for all roads?
            main_road = Road('road_rubber_sticky', rid=road.rid)
            new_x_vals, new_y_vals, z_vals, new_width_vals \
                = _interpolate_nodes(old_x_vals, old_y_vals, old_width_vals, self.add_roads_to_scenario.num_nodes)
            main_nodes = list(zip(new_x_vals, new_y_vals, z_vals, new_width_vals))
            main_road.nodes.extend(main_nodes)
            scenario.add_road(main_road)
            # FIXME Recognize changing widths
            road_width = unique_nodes[0].width
            if road.markings:
                def _calculate_parallel_coords(offset: float, line_width: float) \
                        -> Optional[List[Tuple[float, float, float, float]]]:
                    original_line = LineString(zip(new_x_vals, new_y_vals))
                    try:
                        offset_line = original_line.parallel_offset(offset)
                        coords = offset_line.coords.xy
                    except (NotImplementedError, Exception):  # FIXME Where is TopologyException
                        _logger.exception("Creating an offset line for lane markings failed")
                        return None
                    # NOTE The parallel LineString may have a different number of points than initially given
                    num_coords = len(coords[0])
                    z_vals = repeat(0.01, num_coords)
                    marking_widths = repeat(line_width, num_coords)
                    return list(zip(coords[0], coords[1], z_vals, marking_widths))

                # Draw side lines
                num_lines = road.left_lanes + road.right_lanes + 1
                initial_line_offsets = [d - (road_width / 2) for d in linspace(0, road_width, num=num_lines)]
                side_line_offset = 1.5 * self.add_roads_to_scenario.line_width
                left_side_line = Road('line_white', rid=road.rid + "_left_line")
                left_side_line_nodes = _calculate_parallel_coords(
                    initial_line_offsets[0] + side_line_offset, self.add_roads_to_scenario.line_width)
                if left_side_line_nodes:
                    left_side_line.nodes.extend(left_side_line_nodes)
                    scenario.add_road(left_side_line)
                else:
                    _logger.warning("Could not create left side line")
                right_side_line = Road('line_white', rid=road.rid + "_right_line")
                right_side_line_nodes = _calculate_parallel_coords(
                    initial_line_offsets[-1] - side_line_offset, self.add_roads_to_scenario.line_width)
                if right_side_line_nodes:
                    right_side_line.nodes.extend(right_side_line_nodes)
                    scenario.add_road(right_side_line)
                else:
                    _logger.warning("Could not create right side line")

                # Draw line separating left from right lanes
                if road.left_lanes > 0 and road.right_lanes > 0:
                    offset = initial_line_offsets[road.left_lanes]
                    left_right_divider = Road("line_yellow_double", rid=road.rid + "_left_right_divider")
                    left_right_divider_nodes \
                        = _calculate_parallel_coords(offset, 2 * self.add_roads_to_scenario.line_width)
                    if left_right_divider_nodes:
                        left_right_divider.nodes.extend(left_right_divider_nodes)
                        scenario.add_road(left_right_divider)
                    else:
                        _logger.warning("Could not create line separating lanes having different directions")

                # Draw lines separating left and right lanes from each other
                offset_indices = []
                if road.left_lanes > 1:
                    offset_indices.extend(range(1, road.left_lanes))
                if road.right_lanes > 1:
                    offset_indices.extend(range(road.left_lanes + 1, len(initial_line_offsets) - 1))
                for index in offset_indices:
                    offset = initial_line_offsets[index]
                    lane_separation_line = Road('line_dashed_short', rid=road.rid + "_separator_" + str(index))
                    lane_separation_line_nodes \
                        = _calculate_parallel_coords(offset, self.add_roads_to_scenario.line_width)
                    if lane_separation_line_nodes:
                        lane_separation_line.nodes.extend(lane_separation_line_nodes)
                        scenario.add_road(lane_separation_line)
                    else:
                        _logger.warning("Could not create line separating lanes having the same direction")

    def add_obstacles_to_scenario(self, scenario: Scenario) -> None:
        from beamngpy import ProceduralCone, ProceduralCube, ProceduralCylinder, ProceduralBump, StaticObject
        from dbtypes.scheme import Cone, Cube, Cylinder, Bump, Stopsign, TrafficLightSingle, TrafficLightDouble
        from random import randrange
        for obstacle in self.obstacles:
            obstacle_type = type(obstacle)
            pos = (obstacle.x, obstacle.y, obstacle.z)
            rot = (obstacle.x_rot, obstacle.y_rot, obstacle.z_rot)
            name = obstacle.oid
            mesh = None
            if obstacle_type is Cube:
                mesh = ProceduralCube(pos, rot, (obstacle.length, obstacle.width, obstacle.height), name=name)
            elif obstacle_type is Cylinder:
                mesh = ProceduralCylinder(pos, rot, obstacle.radius, height=obstacle.height, name=name)
            elif obstacle_type is Cone:
                mesh = ProceduralCone(pos, rot, obstacle.base_radius, obstacle.height, name=name)
            elif obstacle_type is Bump:
                mesh = ProceduralBump(pos, rot, obstacle.width, obstacle.length, obstacle.height, obstacle.upper_length,
                                      obstacle.upper_width)
            elif obstacle_type is Stopsign:
                rot = (rot[0], rot[1], 90 - obstacle.z_rot)
                id_number = randrange(1000)
                name_sign = "stopsign" + str(id_number)
                stopsign = StaticObject(pos=(obstacle.x, obstacle.y, obstacle.z), rot=rot, name=name_sign,
                                        scale=(1.9, 1.9, 1.9), shape='/levels/drivebuild/art/objects/stopsign.dae')
                scenario.add_object(stopsign)
            elif obstacle_type is TrafficLightSingle:
                from math import radians, sin, cos
                from numpy import dot
                id_number = randrange(1000)
                name_light = "trafficlight" + str(id_number)
                name_pole = "pole" + str(id_number)
                rot=(rot[0], rot[1], -(obstacle.z_rot) - 90)
                rad_x = radians(rot[0])
                rad_y = radians(rot[1])
                rad_z = radians(rot[2])
                pole_coords = (obstacle.x, obstacle.y, obstacle.z)
                traffic_light_coords = (0, 0, 4.62)         # x y z coordinates when pole is placed at (0,0,0)
                rot_matrix_x = [[1, 0, 0], [0, cos(rad_x), sin(rad_x)], [0, -sin(rad_x), cos(rad_x)]]
                rot_matrix_y = [[cos(rad_y), 0, -sin(rad_y)], [0, 1, 0], [sin(rad_y), 0, cos(rad_y)]]
                rot_matrix_z = [[cos(rad_z), sin(rad_z), 0], [-sin(rad_z), cos(rad_z), 0], [0, 0, 1]]
                rot_matrix = dot(rot_matrix_z, rot_matrix_y)
                rot_matrix = dot(rot_matrix, rot_matrix_x)
                traffic_light_coords = dot(rot_matrix, traffic_light_coords)
                traffic_light_coords = (
                    traffic_light_coords[0] + pole_coords[0], traffic_light_coords[1] + pole_coords[1],
                    traffic_light_coords[2] + pole_coords[2])
                traffic_light = StaticObject(name=name_light, pos=traffic_light_coords, rot=rot,
                                             scale=(1, 1, 1),
                                             shape='/levels/drivebuild/art/objects/trafficlight1a.dae')
                scenario.add_object(traffic_light)
                pole = StaticObject(name=name_pole, pos=pole_coords, rot=rot, scale=(1, 1, 1.1),
                                    shape='/levels/drivebuild/art/objects/pole_traffic1.dae')
                scenario.add_object(pole)
            elif obstacle_type is TrafficLightDouble:
                from math import radians, sin, cos
                from numpy import dot
                id_number = randrange(1000)
                rot = (rot[0], rot[1], -(obstacle.z_rot + 90))
                name_light1 = "trafficlight" + str(id_number)
                name_light2 = "trafficlight" + str(id_number) + 'a'
                name_pole = "pole" + str(id_number)
                rad_x = radians(rot[0])
                rad_y = radians(rot[1])
                rad_z = radians(rot[2])
                pole_coords = (obstacle.x, obstacle.y, obstacle.z)
                traffic_light1_coords = (5.7, 0.17, 5.9)     # x y z coordinates when pole is placed at (0,0,0)
                traffic_light2_coords = (2.1, 0.17, 5.5)
                rot_matrix_x = [[1, 0, 0], [0, cos(rad_x), sin(rad_x)], [0, -sin(rad_x), cos(rad_x)]]
                rot_matrix_y = [[cos(rad_y), 0, -sin(rad_y)], [0, 1, 0], [sin(rad_y), 0, cos(rad_y)]]
                rot_matrix_z = [[cos(rad_z), sin(rad_z), 0], [-sin(rad_z), cos(rad_z), 0], [0, 0, 1]]
                rot_matrix = dot(rot_matrix_z, rot_matrix_y)
                rot_matrix = dot(rot_matrix, rot_matrix_x)
                traffic_light1_coords = dot(rot_matrix, traffic_light1_coords)
                traffic_light1_coords = (
                    traffic_light1_coords[0] + pole_coords[0], traffic_light1_coords[1] + pole_coords[1],
                    traffic_light1_coords[2] + pole_coords[2])
                traffic_light2_coords = dot(rot_matrix, traffic_light2_coords)
                traffic_light2_coords = (
                    traffic_light2_coords[0] + pole_coords[0], traffic_light2_coords[1] + pole_coords[1],
                    traffic_light2_coords[2] + pole_coords[2])

                pole = StaticObject(name=name_pole, pos=pole_coords, rot=rot, scale=(0.75, 0.75, 0.75),
                                     shape='/levels/drivebuild/art/objects/pole_light_signal1.dae')
                scenario.add_object(pole)
                traffic_light1 = StaticObject(name=name_light1, pos=traffic_light1_coords, rot=rot, scale=(1, 1, 1),
                                                shape='/levels/drivebuild/art/objects/trafficlight2a.dae')
                scenario.add_object(traffic_light1)
                traffic_lights2 = StaticObject(name=name_light2, pos=traffic_light2_coords, rot=rot, scale=(1, 1, 1),
                                                 shape='/levels/drivebuild/art/objects/trafficlight2a.dae')
                scenario.add_object(traffic_lights2)
            else:
                _logger.warning(
                    "Obstacles of type " + str(obstacle_type) + " are not supported by the generation, yet.")
                mesh = None
            if mesh:
                # NOTE Procedural meshes use radians for rotation
                scenario.add_procedural_mesh(mesh)

    def add_participants_to_scenario(self, scenario: Scenario) -> None:
        from dbtypes.beamng import DBVehicle
        for participant in self.participants:
            # FIXME Adjust color
            vehicle = DBVehicle(participant.id, model=participant.model, color="White", licence=participant.id)
            for request in participant.ai_requests:
                vehicle.apply_request(request)
            initial_state = participant.initial_state
            # NOTE Participants use degrees for rotation
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
        self.add_roads_to_scenario(scenario)
        self.add_obstacles_to_scenario(scenario)
        self.add_participants_to_scenario(scenario)
        self.add_waypoints_to_scenario(scenario)


def generate_scenario(env: _ElementTree, participants_node: _Element) -> ScenarioBuilder:
    from lxml.etree import _Element
    from dbtypes.scheme import RoadNode, Road, Participant, InitialState, MovementMode, CarModel, WayPoint, Cube, \
        Cylinder, Cone, Bump, Stopsign, TrafficLightSingle, TrafficLightDouble
    from util.xml import xpath, get_tag_name
    from requests import PositionRequest, SpeedRequest, SteeringAngleRequest, CameraRequest, CameraDirection, \
        LidarRequest, RoadCenterDistanceRequest, CarToLaneAngleRequest, BoundingBoxRequest, RoadEdgesRequest

    roads: List[Road] = list()

    @static_vars(prefix="road_", counter=0)
    def _generate_road_id() -> str:
        while True:  # Pseudo "do-while"-loop
            rid = _generate_road_id.prefix + str(_generate_road_id.counter)
            if rid in map(lambda l: l.rid, roads):
                _generate_road_id.counter += 1
            else:
                break
        return rid

    road_nodes = xpath(env, "db:lanes/db:lane")
    for node in road_nodes:
        road_segment_nodes = xpath(node, "db:laneSegment")
        road = Road(list(
            map(
                lambda n: RoadNode((float(n.get("x")), float(n.get("y"))), float(n.get("width"))),
                road_segment_nodes
            )
        ), node.get("markings", "true").lower() == "true",
            int(node.get("leftLanes", "0")),
            int(node.get("rightLanes", "1")),
            node.get("id", _generate_road_id()))
        roads.append(road)

    def get_obstacle_common(node: _Element) -> Tuple[float, float, float, float, float, Optional[str], float]:
        """
        Returns the attributes all types of obstacles have in common.
        :param node: The obstacle node
        :return: x, y, x_rot, y_rot, z_rot, id, z
        """
        return float(node.get("x")), float(node.get("y")), float(node.get("xRot", 0)), float(node.get("yRot", 0)), \
               float(node.get("zRot", 0)), node.get("id", None), node.get("z", 0)

    obstacles = list()
    cube_nodes = xpath(env, "db:obstacles/db:cube")
    for node in cube_nodes:
        x, y, x_rot, y_rot, z_rot, oid, z = get_obstacle_common(node)
        width = float(node.get("width"))
        length = float(node.get("length"))
        height = float(node.get("height"))
        obstacles.append(Cube(x, y, height, width, length, oid, x_rot, y_rot, z_rot, z))

    cylinder_nodes = xpath(env, "db:obstacles/db:cylinder")
    for node in cylinder_nodes:
        x, y, x_rot, y_rot, z_rot, oid, z = get_obstacle_common(node)
        radius = float(node.get("radius"))
        height = float(node.get("height"))
        obstacles.append(Cylinder(x, y, height, radius, oid, x_rot, y_rot, z_rot, z))

    cone_nodes = xpath(env, "db:obstacles/db:cone")
    for node in cone_nodes:
        x, y, x_rot, y_rot, z_rot, oid, z = get_obstacle_common(node)
        base_radius = float(node.get("baseRadius"))
        height = float(node.get("height"))
        obstacles.append(Cone(x, y, height, base_radius, oid, x_rot, y_rot, z_rot, z))

    stopsign_nodes = xpath(env, "db:obstacles/db:stopsign")
    for node in stopsign_nodes:
        x, y, x_rot, y_rot, z_rot, oid, z = get_obstacle_common(node)
        obstacles.append(Stopsign(x, y, oid, x_rot, y_rot, z_rot, z))

    traffic_light_single_nodes = xpath(env, "db:obstacles/db:trafficlightsingle")
    for node in traffic_light_single_nodes:
        x, y, x_rot, y_rot, z_rot, oid, z = get_obstacle_common(node)
        obstacles.append(TrafficLightSingle(x, y, oid, x_rot, y_rot, z_rot, z))

    traffic_light_double_nodes = xpath(env, "db:obstacles/db:trafficlightdouble")
    for node in traffic_light_double_nodes:
        x, y, x_rot, y_rot, z_rot, oid, z = get_obstacle_common(node)
        obstacles.append(TrafficLightDouble(x, y, oid, x_rot, y_rot, z_rot, z))

    bump_nodes = xpath(env, "db:obstacles/db:bump")
    for node in bump_nodes:
        x, y, x_rot, y_rot, z_rot, oid, z = get_obstacle_common(node)
        length = float(node.get("length"))
        width = float(node.get("width"))
        upper_length = float(node.get("upperLength"))
        upper_width = float(node.get("upperWidth"))
        height = float(node.get("height"))
        obstacles.append(Bump(x, y, height, width, length, upper_length, upper_width, oid, x_rot, y_rot, z_rot, z))

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
        # Add data requests declared in the DBC
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
            elif tag == "roadCenterDistance":
                ai_requests.append(RoadCenterDistanceRequest(rid, roads))
            elif tag == "carToLaneAngle":
                ai_requests.append(CarToLaneAngleRequest(rid, roads))
            elif tag == "boundingBox":
                ai_requests.append(BoundingBoxRequest(rid))
            elif tag == "roadEdges":
                ai_requests.append(RoadEdgesRequest(rid))
            else:
                _logger.warning("The tag " + tag + " is not supported, yet.")
        # Add default data requests required for debugging and visualization
        ai_requests.extend([
            BoundingBoxRequest("visualizer_" + pid + "_boundingBox")
        ])
        # Extract the movement of the participant
        movements = list()
        waypoint_nodes = xpath(node, "db:movement/db:waypoint")
        for wp_node in waypoint_nodes:
            common_state_vals = _extract_common_state_vals(wp_node)
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

    return ScenarioBuilder(roads, obstacles, participants, time_of_day)
