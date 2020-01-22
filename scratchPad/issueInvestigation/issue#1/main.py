def main() -> None:
    from drivebuildclient.AIExchangeService import AIExchangeService
    from drivebuildclient.aiExchangeMessages_pb2 import VehicleID
    from common.dummy_ai import DummyAI
    from pathlib import Path
    from os.path import dirname, join
    service = AIExchangeService("localhost", 5000)
    upload_result = service.run_tests("test", "test",
                                      Path(join(dirname(__file__), "providedFiles", "provided.dbc.xml")),
                                      Path(join(dirname(__file__), "providedFiles", "provided.dbe.xml"))
                                      )
    if upload_result and upload_result.submissions:
        for test_name, sid in upload_result.submissions.items():
            vid = VehicleID()
            vid.vid = "ego"
            DummyAI(service).start(sid, vid)


if __name__ == "__main__":
    main()
