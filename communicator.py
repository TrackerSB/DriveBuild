"""
The communicator contains two types of methods:
1. Methods to be called by AIs using micro services (Starting with "ai_")
2. Methods to be called on the server side (Starting with "sim_")
"""
from typing import Dict

from google.protobuf import service_reflection
from google.protobuf.service import Service

from aiExchangeMessages_pb2 import _AIEXCHANGESERVICE, DataResponse, DataRequest, AiID
from dbtypes import AIStatus

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


def ai_request_data(request: DataRequest) -> DataResponse:
    from sim_controller import Simulation
    print("ai_request_data: called")
    data_response = DataResponse()
    data_response.aid.vid.vid = request.aid.vid.vid
    data_response.aid.sid.sid = request.aid.sid.sid
    sims = list(filter(lambda s: s.sid == request.aid.sid.sid, Simulation.running_simulations))
    if sims:
        sim = sims[0]
    else:
        raise ValueError("There is no simulation with ID " + request.aid.sid.sid + " running.")
    for rid in request.request_ids:
        # FIXME Distinguish and convert to request types
        sim.attach_request_data(data_response.data[rid], request.aid.vid.vid, rid)
    print("ai_request_data: terminated")
    return data_response


def sim_request_ai_for(aid: AiID) -> None:
    print("sim_request_ai_for: called")
    while aid.vid.vid not in _registered_ais or _registered_ais[aid.vid.vid] is not AIStatus.WAITING:
        pass
    print("sim_request_ai_for: request ai")
    _registered_ais[aid.vid.vid] = AIStatus.REQUESTED
    while _registered_ais[aid.vid.vid] is AIStatus.REQUESTED:
        pass
    print("sim_request_ai_for: terminated")
