"""
The communicator contains two types of methods:
1. Methods to be called by AIs using micro services (Starting with "ai_")
2. Methods to be called on the server side (Starting with "sim_")
"""
from typing import Dict, List

from google.protobuf import service_reflection
from google.protobuf.service import Service

from dbtypes import AIStatus
from aiExchangeMessages_pb2 import _AIEXCHANGESERVICE, VehicleID, DataResponse, DataRequest, AiID

AIExchangeService = service_reflection.GeneratedServiceType('AIExchangeService', (Service,), dict(
    DESCRIPTOR=_AIEXCHANGESERVICE,
    __module__='aiExchangeMessages_pb2'
))  # FIXME Think about how to correctly implement that

_registered_ais: Dict[str, AIStatus] = {}


def ai_register(vid: str) -> bool:  # FIXME Is this one actually needed
    to_be_registered = vid not in _registered_ais
    if to_be_registered:
        _registered_ais[vid] = AIStatus.READY
    return to_be_registered


def ai_wait_for_simulator_request(aid: AiID) -> None:
    print("ai_wait_for_simulator_request: called")
    _registered_ais[aid.vid.vid] = AIStatus.WAITING
    while _registered_ais[aid.vid.vid] is AIStatus.WAITING:
        pass
    print("ai_wait_for_simulator_request: terminated")


def ai_request_data(request: DataRequest) -> Dict[str, DataResponse.Data]:
    print("ai_request_data: called")
    data = {}
    for rid in request.request_ids:
        pass  # FIXME Implement it
    print("ai_request_data: terminated")
    return data


def sim_request_ai_for(aid: AiID) -> None:
    print("sim_request_ai_for: called")
    while aid.vid.vid not in _registered_ais or _registered_ais[aid.vid.vid] is not AIStatus.WAITING:
        pass
    print("sim_request_ai_for: request ai")
    _registered_ais[aid.vid.vid] = AIStatus.REQUESTED
    while _registered_ais[aid.vid.vid] is AIStatus.REQUESTED:
        pass
    print("sim_request_ai_for: terminated")
