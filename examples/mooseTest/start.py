def _start_moose_test():
    from drivebuildclient.aiExchangeMessages_pb2 import VehicleID
    from drivebuildclient.AIExchangeService import AIExchangeService
    from dummy_ai import DummyAI
    from os.path import dirname, join
    from pathlib import Path
    service = AIExchangeService("localhost", 8383)
    upload_result = service.run_tests("test", "test", Path(join(dirname(__file__), "scenario")))
    if upload_result and upload_result.submissions:
        for test_name, sid in upload_result.submissions.items():
            vid = VehicleID()
            vid.vid = "ego"
            DummyAI(service).start(sid, vid)


if __name__ == "__main__":
    _start_moose_test()
