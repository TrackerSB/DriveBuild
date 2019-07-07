"""
The communicator contains two types of methods:
1. Methods to be called by AIs using micro services (Starting with "ai_")
2. Methods to be called on the server side ALSO using micro services (Starting with "sim_")
"""
from socket import socket
from typing import Dict, List, Optional

from aiExchangeMessages_pb2 import DataResponse, DataRequest, Control, Void, VehicleID
from dbtypes import AIStatus
from sim_controller import Simulation

_registered_ais: Dict[str, Dict[str, AIStatus]] = {}
_client_socket: Optional[socket] = None


def ai_request_data(sim: Simulation, vid: VehicleID, request: DataRequest) -> DataResponse:
    print("ai_request_data: enter")
    data_response = DataResponse()
    for rid in request.request_ids:
        sim.attach_request_data(data_response.data[rid], vid.vid, rid)
    print("ai_request_data: leave")
    return data_response
