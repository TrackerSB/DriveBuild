from drivebuildclient.AIExchangeService import AIExchangeService
from drivebuildclient.aiExchangeMessages_pb2 import SimulationID, VehicleID


class DummyAI:
    def __init__(self, service: AIExchangeService) -> None:
        self._service = service

    def start(self, sid: SimulationID, vid: VehicleID) -> None:
        from drivebuildclient.aiExchangeMessages_pb2 import SimStateResponse, DataRequest
        while True:
            print(sid.sid + ": Test status: " + self._service.get_status(sid))
            sim_state = self._service.wait_for_simulator_request(sid, vid)
            if sim_state is SimStateResponse.SimState.RUNNING:
                request = DataRequest()
                request.request_ids.extend(["egoSpeed"])  # Add all IDs of data to be requested
                data = self._service.request_data(sid, vid, request)
                print(data)
            else:
                print(sid.sid + ": The simulation is not running anymore (Final state: "
                      + SimStateResponse.SimState.Name(sim_state) + ").")
                print(sid.sid + ": Final test result: " + self._service.get_result(sid))
                break
