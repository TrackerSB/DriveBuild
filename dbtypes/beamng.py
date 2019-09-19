from beamngpy import BeamNGpy, Vehicle
from threading import Lock


class DBBeamNGpy(BeamNGpy):
    def __init__(self, host, port, home=None, user=None):
        super().__init__(host, port, home, user)
        self.current_tick = 0
        self.instance_lock = Lock()

    def step(self, count, wait=True):
        self.instance_lock.acquire()
        super().step(count, wait)
        self.instance_lock.release()
        self.current_tick += count

    def poll_sensors(self, vehicle):
        self.instance_lock.acquire()
        super().poll_sensors(vehicle)
        self.instance_lock.release()

    def close(self):
        from msgpack import ExtraData
        from drivebuildclient.common import eprint
        self.instance_lock.acquire()
        try:
            super().close()
        except ExtraData as ex:
            eprint("The close call to BeamNG errored with \"" + str(ex) + "\".")
        self.instance_lock.release()


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
        from drivebuildclient.common import eprint
        if rid in self.requests:
            return self.requests[rid].read_sensor_cache_of(self)
        else:
            eprint("The vehicle " + self.vid + " has no request called " + rid + " attached.")
