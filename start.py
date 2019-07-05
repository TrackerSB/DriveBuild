from socket import socket
from typing import Dict, Optional, List

from aiExchangeMessages_pb2 import SimulationID
from dbtypes import SimulationData
from sim_controller import Simulation

_all_tasks: Dict[Simulation, SimulationData] = {}


def register_at_main_application() -> socket:
    from socket import AF_INET, SOCK_STREAM
    register_socket = socket(AF_INET, SOCK_STREAM)
    register_socket.connect(("localhost", 5001))
    return register_socket


def _get_simulation(sid: SimulationID) -> Optional[Simulation]:
    global _all_tasks
    for sim, _ in _all_tasks.items():
        if sim.sid.sid == sid.sid:
            return sim
    return None


def _get_data(sid: SimulationID) -> Optional[SimulationData]:
    global _all_tasks
    for sim, data in _all_tasks.items():
        if sim.sid.sid == sid.sid:
            return data
    return None


def _run_tests(data: List[bytes]) -> bytes:
    from tc_manager import run_tests
    from warnings import warn
    from aiExchangeMessages_pb2 import SimulationIDs
    global _all_tasks
    file_content = data[0]
    new_tasks = run_tests(file_content)
    sids = SimulationIDs()
    for sim, data in new_tasks.items():
        if sim.sid.sid in [s.sid.sid for s in _all_tasks]:
            warn("The simulation ID " + sim.sid.sid + " already exists and is getting overwritten.")
            _all_tasks.pop(_get_simulation(sim.sid))
        sids.sids.append(sim.sid.sid)
        _all_tasks[sim] = data
    return sids.SerializeToString()


def _status(data: List[bytes]) -> bytes:
    from aiExchangeMessages_pb2 import SimStateResponse, TestResult
    sid = SimulationID()
    sid.ParseFromString(data[0])
    sim = _get_simulation(sid)
    sim_state = SimStateResponse()
    if sim:
        scenario = _get_data(sid).scenario
        if scenario.bng is None:
            task = _get_data(sid).simulation_task
            if task.get_state() is TestResult.Result.SUCCEEDED \
                    or task.get_state() is TestResult.Result.FAILED:
                sim_state.state = SimStateResponse.SimState.FINISHED
            elif task.get_state() is TestResult.Result.SKIPPED:
                sim_state.state = SimStateResponse.SimState.CANCELED
            else:
                sim_state.state = SimStateResponse.SimState.ERRORED  # FIXME Can this be assumed?
        else:
            sim_state.state = SimStateResponse.SimState.RUNNING
    else:
        sim_state.state = SimStateResponse.SimState.UNKNOWN
    return sim_state.SerializeToString()


if __name__ == "__main__":
    from common import eprint
    from aiExchangeMessages_pb2 import Num

    sim_node_register_socket = register_at_main_application()
    # FIXME How to recover failures?
    while True:
        sim_node_register_socket.send(b"ready for action")
        action = sim_node_register_socket.recv(1024)  # FIXME Determine optimal buffer size
        sim_node_register_socket.send(b"ready for num data")
        num_data = Num()
        num_data.ParseFromString(sim_node_register_socket.recv(1024))  # FIXME Determine optimal buffer size
        data = []
        for _ in range(0, num_data.num):
            sim_node_register_socket.send(b"ready for data")
            data.append(sim_node_register_socket.recv(16384))  # FIXME Determine optimal buffer size

        if action == b"runTests":
            result = _run_tests(data)
        elif action == b"status":
            result = _status(data)
        else:
            eprint("The action \"" + action.decode() + "\" is unknown.")
            result = b""  # FIXME How to show errors?

        sim_node_register_socket.send(result)
        result_received = sim_node_register_socket.recv(15)
        if not result_received == b"result received":
            eprint("Expected main application to send \"result received\". Got \"" + result_received.decode() + "\".")
