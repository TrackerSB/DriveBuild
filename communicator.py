"""
The communicator contains two types of methods:
1. Methods to be called by AIs using micro services (Starting with "ai_")
2. Methods to be called on the server side (Starting with "sim_")
"""
from typing import Dict

from google.protobuf import service_reflection
from google.protobuf.service import Service

from dbtypes import AIStatus
from aiExchangeMessages_pb2 import _AIEXCHANGESERVICE

AIExchangeService = service_reflection.GeneratedServiceType('AIExchangeService', (Service,), dict(
    DESCRIPTOR=_AIEXCHANGESERVICE,
    __module__='aiExchangeMessages_pb2'
))

_registered_ais: Dict[str, AIStatus] = {}


def ai_register(vid: str) -> bool:  # FIXME Is this one actually needed
    to_be_registered = vid not in _registered_ais
    if to_be_registered:
        _registered_ais[vid] = AIStatus.READY
    return to_be_registered


def ai_wait_for_simulator_request(vid: str) -> None:
    print("ai_wait_for_simulator_request: called")
    _registered_ais[vid] = AIStatus.WAITING
    while _registered_ais[vid] is AIStatus.WAITING:
        pass
    print("ai_wait_for_simulator_request: terminated")


def sim_request_ai_for(vid: str) -> None:
    print("sim_request_ai_for: called")
    while vid not in _registered_ais or _registered_ais[vid] is not AIStatus.WAITING:
        pass
    print("sim_request_ai_for: request ai")
    _registered_ais[vid] = AIStatus.REQUESTED
    while _registered_ais[vid] is AIStatus.REQUESTED:
        pass
    print("sim_request_ai_for: terminated")
