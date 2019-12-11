from AIExchangeService import AIExchangeService
from drivebuildclient.aiExchangeMessages_pb2 import SimulationID, TestResult

if __name__ == "__main__":
    sid = SimulationID()
    sid.sid = "<ID of simulation>"
    result = TestResult()
    result.result = TestResult.Result.FAILED
    AIExchangeService("localhost", 8383).control_sim(sid, result)
