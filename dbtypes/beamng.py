from beamngpy import Vehicle
from logging import getLogger

_logger = getLogger("DriveBuild.SimNode.DBTypes.BeamNG")


class DBVehicle(Vehicle):
    from requests import AiRequest
    from typing import Any

    def __init__(self, vid: str, **options) -> None:
        super().__init__(vid, **options)
        self.requests = {}

    def apply_request(self, request: AiRequest) -> None:
        self.requests[request.rid] = request
        request.add_sensor_to(self)

    def poll_request(self, rid: str) -> Any:
        """
        The return type depends on the return type of the appropriate AIRequest.
        """
        if rid in self.requests:
            return self.requests[rid].read_sensor_cache_of(self)
        else:
            _logger.warning("The vehicle " + self.vid + " has no request called " + rid + " attached.")
