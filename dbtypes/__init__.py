from datetime import datetime
from enum import Enum
from threading import Thread

from beamngpy import Scenario
from dataclasses import dataclass
from lxml.etree import _ElementTree

from aiExchangeMessages_pb2 import TestResult


class AIStatus(Enum):
    READY = "READY"
    WAITING = "WAITING"
    REQUESTED = "REQUESTED"


class ExtThread:
    """
    Wraps a Thread and allows to set the returned status manually.
    """

    _state_to_str = {
        0: "TEST SUCCEEDED",
        1: "TEST FAILED",
        2: "TEST SKIPPED"
    }

    def __init__(self, thread: Thread):
        self.thread = thread
        self._status = None

    def state(self) -> str:
        thread_state = "ALIVE" if self.thread.is_alive() else "NOT ALIVE"
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
    start_time: datetime = None
    end_time: datetime = None
    result: TestResult.Result = None
