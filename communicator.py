"""
The communicator contains two types of methods:
1. Methods to be called by AIs using micro services (Starting with "ai_")
2. Methods to be called on the server side (Starting with "sim_")
"""
from typing import Dict

from google.protobuf import service_reflection
from google.protobuf.service import Service

from aiExchangeMessages_pb2 import _AIEXCHANGESERVICE, DataResponse, DataRequest, AiID, Control, Void
from dbtypes import AIStatus
from sim_controller import Simulation

AIExchangeService = service_reflection.GeneratedServiceType('AIExchangeService', (Service,), dict(
    DESCRIPTOR=_AIEXCHANGESERVICE,
    __module__='aiExchangeMessages_pb2'
))  # FIXME Think about how to correctly implement that

_registered_ais: Dict[str, AIStatus] = {}


def ai_wait_for_simulator_request(aid: AiID) -> None:
    print("ai_wait_for_simulator_request: called")
    _registered_ais[aid.vid.vid] = AIStatus.WAITING
    while _registered_ais[aid.vid.vid] is AIStatus.WAITING:
        pass
    print("ai_wait_for_simulator_request: terminated")


def _get_simulation(sid: str) -> Simulation:
    sims = list(filter(lambda s: s.sid == sid, Simulation.running_simulations))
    if sims:
        return sims[0]
    else:
        raise ValueError("There is no simulation with ID " + sid + " running.")


def ai_request_data(request: DataRequest) -> DataResponse:
    print("ai_request_data: called")
    data_response = DataResponse()
    data_response.aid.vid.vid = request.aid.vid.vid
    data_response.aid.sid.sid = request.aid.sid.sid
    sim = _get_simulation(request.aid.sid.sid)
    for rid in request.request_ids:
        sim.attach_request_data(data_response.data[rid], request.aid.vid.vid, rid)
    print("ai_request_data: terminated")
    return data_response


def ai_control(control: Control) -> Void:
    sim = _get_simulation(control.aid.sid.sid)
    command_type = control.WhichOneof("command")
    if command_type == "simCommand":
        sim.control_sim(control.simCommand)
    elif command_type == "avCommand":
        command = control.avCommand
        sim.control_av(control.aid.vid.vid, command.accelerate, command.steer, command.brake)
    else:
        raise NotImplementedError("Interpreting commands of type " + command_type + " is not implemented, yet.")
    return Void()


def sim_request_ai_for(aid: AiID) -> None:
    print("sim_request_ai_for: called")
    while aid.vid.vid not in _registered_ais or _registered_ais[aid.vid.vid] is not AIStatus.WAITING:
        pass
    print("sim_request_ai_for: request ai")
    _registered_ais[aid.vid.vid] = AIStatus.REQUESTED
    while _registered_ais[aid.vid.vid] is AIStatus.REQUESTED:
        pass
    print("sim_request_ai_for: terminated")
