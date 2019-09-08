from datetime import datetime
from enum import Enum
from threading import Thread

from beamngpy import Scenario
from dataclasses import dataclass
from lxml.etree import _ElementTree

from drivebuildclient.aiExchangeMessages_pb2 import TestResult, User, SimulationID


class ExtThread:
    """
    Wraps a Thread such that this object can be serialized and allows to set the returned status manually.
    """

    _state_to_str = {
        0: "TEST SUCCEEDED",
        1: "TEST FAILED",
        2: "TEST SKIPPED"
    }

    def __init__(self, thread_id: int):
        self.thread_id = thread_id
        self._status = None

    def _get_thread(self) -> Thread:
        import threading
        for thread in threading.enumerate():
            if thread.ident == self.thread_id:
                return thread
        raise ValueError("Could not find thread with id " + str(self.thread_id) + ".")

    def state(self) -> str:
        thread_state = "ALIVE" if self._get_thread().is_alive() else "NOT ALIVE"
        return thread_state if self._status is None else ExtThread._state_to_str[self._status]

    def get_state(self) -> TestResult.Result:
        """
        Returns the manually set state or None if no state was set manually.
        """
        return self._status

    def set_state(self, status: TestResult.Result) -> None:
        """
        Passing None as status makes disables a manually set status.
        """
        self._status = status


@dataclass
class SimulationData:
    scenario: Scenario
    simulation_task: ExtThread
    criteria: _ElementTree
    environment: _ElementTree
    sid: SimulationID
    start_time: datetime = None
    end_time: datetime = None
    user: User = None
