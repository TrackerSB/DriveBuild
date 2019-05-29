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


class DamageRequest(AiRequest):
    from beamngpy import Vehicle

    def add_sensor_to(self, vehicle: Vehicle) -> None:
        from beamngpy.sensors import Damage
        vehicle.attach_sensor(self.rid, Damage())  # FIXME Is Electrics sensor needed?

    def read_sensor_cache_of(self, vehicle: Vehicle) -> bool:
        print("Damage: " + str(vehicle.poll_sensors(self.rid)))  # FIXME Implement DamageSensor
        return False


class SteeringAngleRequest(AiRequest):
    from beamngpy import Vehicle

    def add_sensor_to(self, _: Vehicle) -> None:
        pass

    def read_sensor_cache_of(self, vehicle: Vehicle) -> float:
        # FIXME Implement getting steering angle
        return None


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
        from util import eprint
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
