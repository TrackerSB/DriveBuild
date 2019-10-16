from logging import getLogger
from os.path import join
from queue import Queue
from threading import Lock

from beamngpy import BeamNGpy

from config import BEAMNG_USER_PATH, BEAMNG_INSTALL_FOLDER

_logger = getLogger("DriveBuild.SimNode.DBTypes.BeamNGpy")


class DBBeamNGpy(BeamNGpy):
    user_path_pool = Queue()
    num_created_user_paths = 0

    def __init__(self, host, port):
        from pathlib import Path
        if DBBeamNGpy.user_path_pool.empty():
            user_path = join(BEAMNG_USER_PATH, "drivebuild_" + str(DBBeamNGpy.num_created_user_paths))
            DBBeamNGpy.num_created_user_paths = DBBeamNGpy.num_created_user_paths + 1
        else:
            user_path = DBBeamNGpy.user_path_pool.get()
        Path(user_path).mkdir(parents=True, exist_ok=True)
        super().__init__(host, port, BEAMNG_INSTALL_FOLDER, user_path)
        self.current_tick = 0
        self._sim_lock = Lock()

    def step(self, count, wait=True):
        self._sim_lock.acquire()
        super().step(count, wait)
        self._sim_lock.release()
        self.current_tick += count

    def poll_sensors(self, vehicle):
        if self.skt:
            try:
                super().poll_sensors(vehicle)
            except Exception:
                _logger.exception("Polling sensors failed")

    def close(self):
        try:
            self._sim_lock.acquire()
            super().close()
            self._sim_lock.release()
            DBBeamNGpy.user_path_pool.put(self.user)
        except Exception:
            _logger.exception("Closing a BeamNG instance failed.")

    def get_road_edges(self, road):
        try:
            self._sim_lock.acquire()
            result = super().get_road_edges(road)
            self._sim_lock.release()
            return result
        except Exception:
            _logger.exception("Requesting road edges failed")
