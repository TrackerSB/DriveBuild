from typing import Optional

from beamngpy import Vehicle
from logging import getLogger

_logger = getLogger("DriveBuild.SimNode.DBTypes.BeamNG")


class DBVehicle(Vehicle):
    from requests import AiRequest
    from typing import Any

    def __init__(self, vid: str, **options) -> None:
        from threading import Lock
        super().__init__(vid, **options)
        self.requests = {}
        self._vehicle_lock = Lock()

    def poll_sensors(self, requests):
        _logger.debug(self.vid + ": Try acquire lock for polling sensors")
        self._vehicle_lock.acquire()
        _logger.debug(self.vid + ": Acquired lock for polling sensors")
        result = super().poll_sensors(requests)
        _logger.debug(self.vid + ": Release lock for polling sensors")
        self._vehicle_lock.release()
        return result

    def control(self, **options):
        _logger.debug(self.vid + ": Try acquire lock for controlling")
        self._vehicle_lock.acquire()
        _logger.debug(self.vid + ": Acquired lock for controlling")
        if self.skt:
            super().control(**options)
        else:
            _logger.warning("The vehicle can not be controlled since it is not connected")
        _logger.debug(self.vid + ": Release lock for controlling")
        self._vehicle_lock.release()

    def close(self):
        _logger.debug(self.vid + ": Try acquire lock for controlling")
        self._vehicle_lock.acquire()
        _logger.debug(self.vid + ": Acquired lock for controlling")
        if self.skt:
            super().close()
        else:
            _logger.warning("The connection to the vehicle " + self.vid + "could not be closed")
        self._vehicle_lock.release()

    def apply_request(self, request: AiRequest) -> None:
        self.requests[request.rid] = request
        request.add_sensor_to(self)

    def poll_request(self, rid: str) -> Optional[Any]:
        """
        The return type depends on the return type of the appropriate AIRequest.
        """
        if rid in self.requests:
            return self.requests[rid].read_sensor_cache_of(self)
        else:
            _logger.warning("The vehicle " + self.vid + " has no request called " + rid + " attached.")
