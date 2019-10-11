from os.path import join
from queue import Queue
from threading import Lock

from beamngpy import BeamNGpy

from config import BEAMNG_USER_PATH, BEAMNG_INSTALL_FOLDER


class DBBeamNGpy(BeamNGpy):
    user_path_pool = Queue()
    num_created_user_paths = 0

    def __init__(self, host, port):
        from pathlib import Path
        if DBBeamNGpy.user_path_pool.empty():
            user_path = join(BEAMNG_USER_PATH, "drivebuild_" + str(DBBeamNGpy.num_created_user_paths))
            DBBeamNGpy.num_created_user_paths = DBBeamNGpy.num_created_user_paths + 1
        else:
            user_path = DBBeamNGpy.user_path_pool.get().name
        Path(user_path).mkdir(parents=True, exist_ok=True)
        super().__init__(host, port, BEAMNG_INSTALL_FOLDER, user_path)
        self.current_tick = 0
        self.instance_lock = Lock()

    def step(self, count, wait=True):
        self.instance_lock.acquire()
        super().step(count, wait)
        self.instance_lock.release()
        self.current_tick += count

    def poll_sensors(self, vehicle):
        self.instance_lock.acquire()
        if self.skt:
            try:
                super().poll_sensors(vehicle)
            except Exception as ex:
                raise BeamNGpyException("Polling sensors failed") from ex
            finally:
                self.instance_lock.release()
        else:
            self.instance_lock.release()

    def close(self):
        self.instance_lock.acquire()
        try:
            super().close()
            DBBeamNGpy.user_path_pool.put(self.user)
        except Exception as ex:
            raise BeamNGpyException("Closing BeamNG failed") from ex
        self.instance_lock.release()


class BeamNGpyException(RuntimeWarning):
    pass