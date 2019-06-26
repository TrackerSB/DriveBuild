"""
The communicator contains two types of methods:
1. Methods to be called by AIs using micro services (Starting with "ai_")
2. Methods to be called on the server side ALSO using micro services (Starting with "sim_")
"""
from typing import Dict

from aiExchangeMessages_pb2 import DataResponse, DataRequest, Control, Void, VehicleID, SimulationID
from dbtypes import AIStatus
from sim_controller import Simulation

_registered_ais: Dict[str, Dict[str, AIStatus]] = {}


def ai_wait_for_simulator_request(sid: SimulationID, vid: VehicleID) -> None:
    from app import is_simulation_running
    print("ai_wait_for_simulator_request: enter")
    if sid.sid not in _registered_ais:
        _registered_ais[sid.sid] = {}
    _registered_ais[sid.sid][vid.vid] = AIStatus.WAITING
    while is_simulation_running(sid) and _registered_ais[sid.sid][vid.vid] is AIStatus.WAITING:
        pass
    print("ai_wait_for_simulator_request: leave")


def ai_request_data(sim: Simulation, vid: VehicleID, request: DataRequest) -> DataResponse:
    print("ai_request_data: enter")
    data_response = DataResponse()
    for rid in request.request_ids:
        sim.attach_request_data(data_response.data[rid], vid.vid, rid)
    print("ai_request_data: leave")
    return data_response


def ai_control(sim: Simulation, vid: VehicleID, control: Control) -> Void:
    from app import control_sim
    print("ai_control: enter")
    command_type = control.WhichOneof("command")
    if command_type == "simCommand":
        control_sim(sim, control.simCommand, True)
    elif command_type == "avCommand":
        command = control.avCommand
        sim.control_av(vid.vid, command.accelerate, command.steer, command.brake)
    else:
        raise NotImplementedError("Interpreting commands of type " + command_type + " is not implemented, yet.")
    print("ai_control: leave")
    return Void()


def sim_request_ai_for(sid: SimulationID, vid: VehicleID) -> None:
    print("sim_request_ai_for: enter")
    while sid.sid not in _registered_ais \
            or vid.vid not in _registered_ais[sid.sid] \
            or _registered_ais[sid.sid][vid.vid] is not AIStatus.WAITING:
        pass
    _registered_ais[sid.sid][vid.vid] = AIStatus.REQUESTED
    print("sim_request_ai_for: requested")
    while _registered_ais[sid.sid][vid.vid] is AIStatus.REQUESTED:
        pass
    print("sim_request_ai_for: leave")
