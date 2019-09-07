from abc import ABC
from enum import Enum


class AiRequest(ABC):
    from abc import abstractmethod
    from beamngpy import Vehicle
    from typing import Any

    def __init__(self, rid: str):
        self.rid = rid

    @abstractmethod
    def add_sensor_to(self, vehicle: Vehicle) -> None:
        pass

    @abstractmethod
    def read_sensor_cache_of(self, vehicle: Vehicle) -> Any:
        """
        This method returns the data the request represents. NOTE It does not call poll_sensors or similar!
        :param vehicle: The vehicle to read the cached sensor data from.
        :return: The data to be retrieved by this request.
        """
        pass


class PositionRequest(AiRequest):
    from beamngpy import Vehicle
    from typing import Tuple

    def add_sensor_to(self, _: Vehicle) -> None:
        pass

    def read_sensor_cache_of(self, vehicle: Vehicle) -> Tuple[float, float]:
        x, y, _ = vehicle.state["pos"]
        return x, y


class BoundingBoxRequest(AiRequest):
    from beamngpy import Vehicle
    from shapely.geometry import Polygon

    def add_sensor_to(self, vehicle: Vehicle) -> None:
        pass

    def read_sensor_cache_of(self, vehicle: Vehicle) -> Polygon:
        from shapely.geometry import Polygon
        bbox_points = vehicle.get_bbox()
        shell = tuple(map(lambda pos: bbox_points[pos][0:2],
                          ["near_bottom_left", "far_bottom_left", "far_bottom_right", "near_bottom_right"]))
        return Polygon(shell=shell)


class DamageRequest(AiRequest):
    from beamngpy import Vehicle

    def add_sensor_to(self, vehicle: Vehicle) -> None:
        from beamngpy.sensors import Damage
        vehicle.attach_sensor(self.rid, Damage())

    def read_sensor_cache_of(self, vehicle: Vehicle) -> bool:
        # FIXME Any more precise way of checking damage?
        return vehicle.sensor_cache[self.rid]["damage"] > 0


class SteeringAngleRequest(AiRequest):
    from beamngpy import Vehicle

    def add_sensor_to(self, _: Vehicle) -> None:
        pass

    def read_sensor_cache_of(self, vehicle: Vehicle) -> float:
        from numpy import arctan2, rad2deg
        # FIXME What´s the up vector?
        direction = vehicle.state["dir"]  # FIXME This value is likely not what a user expects
        return rad2deg(arctan2(direction[1], direction[0]))


class SpeedRequest(AiRequest):
    """
    Given in m/s
    """
    from beamngpy import Vehicle

    def add_sensor_to(self, _: Vehicle) -> None:
        pass

    def read_sensor_cache_of(self, vehicle: Vehicle) -> float:
        from numpy.linalg import norm
        return norm(vehicle.state["vel"])


class LidarRequest(AiRequest):
    from beamngpy import Vehicle
    from numpy import ndarray
    # FIXME Which parameters to allow?

    def __init__(self, rid: str, max_dist: int) -> None:
        super().__init__(rid)
        self.max_dist = max_dist

    def add_sensor_to(self, vehicle: Vehicle) -> None:
        from beamngpy.sensors import Lidar
        vehicle.attach_sensor(self.rid, Lidar(max_dist=self.max_dist))

    def read_sensor_cache_of(self, vehicle: Vehicle) -> ndarray:
        return vehicle.sensor_cache[self.rid]["points"]


class CameraDirection(Enum):
    FRONT = "FRONT"
    RIGHT = "RIGHT"
    BACK = "BACK"
    LEFT = "LEFT"
    DASH = "DASH"


class CameraRequest(AiRequest):
    from beamngpy import Vehicle
    from typing import Tuple
    from PIL.Image import Image

    def __init__(self, rid: str, width: int, height: int, fov: int, direction: CameraDirection):
        super().__init__(rid)
        self.width = width
        self.height = height
        self.fov = fov
        self.direction = direction

    def add_sensor_to(self, vehicle: Vehicle) -> None:
        from beamngpy.sensors import Camera
        from cmath import pi
        from drivebuildclient.common import eprint
        # NOTE rotation range: -pi to pi
        # NOTE Reference point is the point of the model
        # NOTE First rotate camera, then shift based on rotated axis of the camera
        # NOTE x-axis points rightwards, y-axis points forwards, z-axis points upwards
        # FIXME These values are specialized for etk800
        if self.direction is CameraDirection.FRONT:
            x_pos = -0.3
            y_pos = 2.1
            z_pos = 0.3
            x_rot = 0
            y_rot = pi
            z_rot = 0
        elif self.direction is CameraDirection.RIGHT:
            x_pos = 0
            y_pos = 0.5
            z_pos = 0.3
            x_rot = pi
            y_rot = 0
            z_rot = 0
        elif self.direction is CameraDirection.BACK:
            x_pos = 0
            y_pos = 2.6
            z_pos = 0.3
            x_rot = 0
            y_rot = -pi
            z_rot = 0
        elif self.direction is CameraDirection.LEFT:
            x_pos = 0
            y_pos = 1.2
            z_pos = 0.3
            x_rot = -pi
            y_rot = 0
            z_rot = 0
        elif self.direction is CameraDirection.DASH:
            x_pos = 0
            y_pos = 0.4
            z_pos = 1
            x_rot = 0
            y_rot = pi
            z_rot = 0
        else:
            eprint("The camera direction " + str(self.direction.value) + " is not implemented.")
            return
        vehicle.attach_sensor(self.rid,
                              Camera((x_pos, y_pos, z_pos), (x_rot, y_rot, z_rot), self.fov, (self.width, self.height),
                                     colour=True, depth=True, annotation=False))

    def read_sensor_cache_of(self, vehicle: Vehicle) -> Tuple[Image, Image, Image]:
        """
        Returns the colored, annotated and the depth image.
        """
        data = vehicle.sensor_cache[self.rid]
        return data["colour"], data["annotation"], data["depth"]


class LightRequest(AiRequest):
    from beamngpy import Vehicle
    from dbtypes.scheme import CarLight

    def add_sensor_to(self, vehicle: Vehicle) -> None:
        from beamngpy.sensors import Electrics
        vehicle.attach_sensor(self.rid, Electrics())

    def read_sensor_cache_of(self, vehicle: Vehicle) -> CarLight:
        # FIXME How to get lights?
        return None


class LaneCenterDistanceRequest(AiRequest):
    from beamngpy import Vehicle
    from typing import Tuple, List, Optional, Any
    # from dbtypes.scheme import Lane  # FIXME Cannot import Lane

    def __init__(self, rid: str, lanes: List[Any]):  # lanes: List[Lane]
        from shapely.geometry import LineString, Point
        super().__init__(rid)
        self.lane_lines = {}
        for lane in lanes:
            lane_line = LineString([Point(node.position[0], node.position[1]) for node in lane.nodes])
            self.lane_lines[lane.lid] = lane_line

    def add_sensor_to(self, vehicle: Vehicle) -> None:
        pass

    def read_sensor_cache_of(self, vehicle: Vehicle) -> Tuple[Optional[str], Optional[float]]:
        from shapely.geometry import Point
        x, y, _ = vehicle.state["pos"]
        car_pos = Point(x, y)
        lane_id = None
        min_dist = None
        for cur_lane_id, cur_lane in self.lane_lines.items():
            cur_dist = cur_lane.distance(car_pos)
            if not min_dist or cur_dist < min_dist:
                lane_id = cur_lane_id
                min_dist = cur_dist
        return lane_id, min_dist


class CarToLaneAngleRequest(AiRequest):
    from beamngpy import Vehicle
    from typing import Tuple, Any, List
    # from dbtypes.scheme import Lane  # FIXME Can not import Lane

    def __init__(self, rid: str, lanes: List[Any]):  # lanes: List[Lane]
        from shapely.geometry import LineString, Point
        super().__init__(rid)
        self.lane_lines = {}
        for lane in lanes:
            lane_line = LineString([Point(node.position[0], node.position[1]) for node in lane.nodes])
            self.lane_lines[lane.lid] = lane_line

    def add_sensor_to(self, vehicle: Vehicle) -> None:
        pass

    def read_sensor_cache_of(self, vehicle: Vehicle) -> Tuple[str, float]:
        from shapely.geometry import Point, LineString
        from numpy import rad2deg, arctan2, array
        x, y, _ = vehicle.state["pos"]
        car_pos = Point(x, y)
        x_dir, y_dir, _ = vehicle.state["dir"]
        car_angle = rad2deg(arctan2(y_dir, x_dir))
        min_dist = None
        angle_diff = None
        lane_id = None
        for cur_lane_id, cur_lane in self.lane_lines.items():
            cur_coord = cur_lane.coords[0]
            for i in range(1, len(cur_lane.coords)):
                next_coord = cur_lane.coords[i]
                cur_line = LineString([cur_coord, next_coord])
                cur_dist = cur_line.distance(car_pos)
                if not min_dist or cur_dist < min_dist:
                    min_dist = cur_dist
                    diff = array(next_coord) - array(cur_coord)
                    cur_angle = rad2deg(arctan2(diff[1], diff[0]))
                    angle_diff = car_angle - cur_angle
                    lane_id = cur_lane_id
                cur_coord = next_coord
        return lane_id, angle_diff
