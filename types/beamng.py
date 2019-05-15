from beamngpy import Road, BeamNGpy


class DBRoad(Road):
    def __init__(self, id: str, material, **options):
        super().__init__(material, **options)
        self.id = id


class DBBeamNGpy(BeamNGpy):
    def __init__(self, host, port, home=None, user=None):
        super().__init__(host, port, home, user)
        self.current_tick = 0

    def step(self, count, wait=True):
        super().step(count, wait)
        self.current_tick += 1
