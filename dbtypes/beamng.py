from beamngpy import Road, BeamNGpy, Vehicle


class DBRoad(Road):
    def __init__(self, rid: str, material: str, **options):
        super().__init__(material, one_way=True, **options)
        self.rid = rid


class DBBeamNGpy(BeamNGpy):
    def __init__(self, host, port, home=None, user=None):
        super().__init__(host, port, home, user)
        self.current_tick = 0

    def step(self, count, wait=True):
        super().step(count, wait)
        self.current_tick += 1


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
        from util import eprint
        if rid in self.requests:
            return self.requests[rid].read_sensor_cache_of(self)
        else:
            eprint("The vehicle " + self.vid + " has no request called " + rid + " attached.")
