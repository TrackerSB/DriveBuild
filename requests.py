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
    def poll_sensor_of(self, vehicle: Vehicle) -> Any:
        pass


class PositionRequest(AiRequest):
    from beamngpy import Vehicle
    from typing import Tuple

    def add_sensor_to(self, _: Vehicle) -> None:
        pass

    def poll_sensor_of(self, vehicle: Vehicle) -> Tuple[float, float]:
        vehicle.update_vehicle()
        x, y, _ = vehicle.state["pos"]
        return x, y


class DamageRequest(AiRequest):
    from beamngpy import Vehicle

    def add_sensor_to(self, vehicle: Vehicle) -> None:
        from beamngpy.sensors import Damage
        vehicle.attach_sensor(self.rid, Damage())  # FIXME Is Electrics sensor needed?

    def poll_sensor_of(self, vehicle: Vehicle) -> bool:
        print("Damage: " + str(vehicle.poll_sensors(self.rid)))  # FIXME Implement DamageSensor
        return False


class SteeringAngleRequest(AiRequest):
    from beamngpy import Vehicle

    def add_sensor_to(self, _: Vehicle) -> None:
        pass

    def poll_sensor_of(self, vehicle: Vehicle) -> float:
        vehicle.update_vehicle()
        # FIXME Implement getting steering angle
        return None


class SpeedRequest(AiRequest):
    """
    Given in m/s
    """
    from beamngpy import Vehicle

    def add_sensor_to(self, _: Vehicle) -> None:
        pass

    def poll_sensor_of(self, vehicle: Vehicle) -> float:
        from numpy.linalg import norm
        vehicle.update_vehicle()
        return norm(vehicle.state["vel"])


class LidarRequest(AiRequest):
    from beamngpy import Vehicle
    from typing import Any
    # FIXME Which parameters to allow?

    def add_sensor_to(self, vehicle: Vehicle) -> None:
        from beamngpy.sensors import Lidar
        vehicle.attach_sensor(self.rid, Lidar())

    def poll_sensor_of(self, vehicle: Vehicle) -> Any:
        # FIXME Which return type?
        return vehicle.poll_sensors(self.rid)


class CameraDirection(Enum):
    FRONT = "FRONT"
    RIGHT = "RIGHT"
    BACK = "BACK"
    LEFT = "LEFT"


class CameraRequest(AiRequest):
    from beamngpy import Vehicle
    from typing import Any

    def __init__(self, rid: str, width: int, height: int, direction: CameraDirection):
        super().__init__(rid)
        self.width = width
        self.height = height
        self.direction = direction

    def add_sensor_to(self, vehicle: Vehicle) -> None:
        from beamngpy.sensors import Camera
        # TODO Provide annotated data?
        x_pos = y_pos = z_pos = 0
        x_rot = y_rot = z_rot = 0
        fov = 0  # FIXME What does this do?
        if self.direction is CameraDirection.FRONT:  # FIXME Implement attachment
            pass
        vehicle.attach_sensor(self.rid,
                              Camera((x_pos, y_pos, z_pos), (x_rot, y_rot, z_rot), fov, (self.width, self.height),
                                     annotation=False))

    def poll_sensor_of(self, vehicle: Vehicle) -> Any:
        return vehicle.poll_sensors(self.rid)  # FIXME What is returned? # FIXME This call just blocks


class LightRequest(AiRequest):
    from beamngpy import Vehicle
    from dbtypes.scheme import CarLight

    def add_sensor_to(self, vehicle: Vehicle) -> None:
        from beamngpy.sensors import Electrics
        vehicle.attach_sensor(self.rid, Electrics())

    def poll_sensor_of(self, vehicle: Vehicle) -> CarLight:
        # FIXME How to get lights?
        return None
