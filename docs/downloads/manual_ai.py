from threading import Thread
from typing import List
from pathlib import Path

from drivebuildclient.aiExchangeMessages_pb2 import SimulationID


def _handle_vehicle(sid: SimulationID, vid: str, requests: List[str]) -> None:
    vid_obj = VehicleID()
    vid_obj.vid = vid

    while True:
        print(sid.sid + ": Test status: " + service.get_status(sid))
        print(vid + ": Wait")
        sim_state = service.wait_for_simulator_request(sid, vid_obj)  # wait()
        if sim_state is SimStateResponse.SimState.RUNNING:
            print(vid + ": Request data")
            request = DataRequest()
            request.request_ids.extend(requests)
            data = service.request_data(sid, vid_obj, request)  # request()
            # print(data)
            print(vid + ": Wait for control")
            control = Control()
            while not is_pressed("space"):  # Wait for the user to trigger manual drive
                pass
            print(vid + ": Control")
            if is_pressed("s"):
                control.simCommand.command = Control.SimCommand.Command.SUCCEED
            elif is_pressed("f"):
                control.simCommand.command = Control.SimCommand.Command.FAIL
            elif is_pressed("c"):
                control.simCommand.command = Control.SimCommand.Command.CANCEL
            else:
                accelerate = 0
                steer = 0
                brake = 0
                if is_pressed("up"):
                    accelerate = 1
                if is_pressed("down"):
                    brake = 1
                if is_pressed("right"):
                    steer = steer + 1
                if is_pressed("left"):
                    steer = steer - 1
                control.avCommand.accelerate = accelerate
                control.avCommand.steer = steer
                control.avCommand.brake = brake
            service.control(sid, vid_obj, control)  # control()
        else:
            print(sid.sid + ": The simulation is not running anymore (State: "
                  + SimStateResponse.SimState.Name(sim_state) + ").")
            print(sid.sid + ": Final result: " + service.get_result(sid))
            break


if __name__ == "__main__":
    from drivebuildclient.AIExchangeService import AIExchangeService
    from drivebuildclient.aiExchangeMessages_pb2 import SimStateResponse, Control, SimulationID, VehicleID, DataRequest
    from keyboard import is_pressed

    service = AIExchangeService("localhost", 8383)

    # Send tests
    submission_result = service.run_tests("test", "test", Path("criteriaA.dbc.xml"), Path("environmentA.dbe.xml"))

    # Interact with a simulation
    if submission_result and submission_result.submissions:
        for test_name, sid in submission_result.submissions.items():
            ego_requests = ["egoPosition", "egoSpeed", "egoSteeringAngle", "egoFrontCamera", "egoLidar", "egoLaneDist"]
            non_ego_requests = ["nonEgoPosition", "nonEgoSpeed", "nonEgoSteeringAngle", "nonEgoLeftCamera", "nonEgoLidar",
                                "nonEgoLaneDist"]
            ego_vehicle = Thread(target=_handle_vehicle, args=(sid, "ego", ego_requests))
            ego_vehicle.start()
            non_ego_vehicle = Thread(target=_handle_vehicle, args=(sid, "nonEgo", non_ego_requests))
            non_ego_vehicle.start()
            ego_vehicle.join()
            non_ego_vehicle.join()
