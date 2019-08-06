import copyreg

from lxml.etree import _Element


# Register pickler for _Element
def element_unpickler(data: bytes) -> _Element:
    from io import BytesIO
    from lxml.etree import parse
    return parse(BytesIO(data)).getroot()


def element_pickler(element: _Element):
    from lxml.etree import tostring
    return element_unpickler, (tostring(element),)


copyreg.pickle(_Element, element_pickler, element_unpickler)

if __name__ == "__main__":
    from aiExchangeMessages_pb2 import SimulationID, VehicleIDs, Void, VerificationResult, SimulationNodeID, \
        VehicleID, Num, SimulationIDs, SimStateResponse, TestResult, Control, DataRequest, DataResponse, User, \
        MaySimulationIDs
    from common import eprint, create_client, process_messages, accept_at_server, create_server
    from config import MAIN_APP_PORT, MAIN_APP_HOST, SIM_NODE_PORT
    from threading import Thread
    from dbtypes import AIStatus, SimulationData
    from dbtypes.scheme import MovementMode
    from typing import Optional, List, Tuple, Dict, Any
    from socket import socket
    from db_handler import get_connection
    from sim_controller import Simulation

    _all_tasks: Dict[Simulation, SimulationData] = {}
    _registered_ais: Dict[str, Dict[str, AIStatus]] = {}
    _dbms_connection = get_connection()


    def _get_simulation(sid: SimulationID) -> Optional[Simulation]:
        for sim, _ in _all_tasks.items():
            if sim.sid.sid == sid.sid:
                return sim
        return None


    def _get_data(sid: SimulationID) -> Optional[SimulationData]:
        for sim, data in _all_tasks.items():
            if sim.sid.sid == sid.sid:
                return data
        return None


    def _is_simulation_running(sid: SimulationID) -> bool:
        while True:  # Pseudo "do-while"-loop
            data = _get_data(sid)
            if data:
                break
        return data.scenario.bng is not None


    # Actions to be requested by the SimNode itself (not a simulation)
    def _generate_sid() -> SimulationID:
        from random import randint
        while True:  # Pseudo "do-while"-loop
            sid = prefix + "_sim_" + str(randint(0, 10000))
            sid_obj = SimulationID()
            sid_obj.sid = sid
            if _get_simulation(sid_obj) is None:
                break
        return sid_obj


    def _handle_sim_node_message(conn: socket, _: Tuple[str, int]) -> None:
        from common import process_message
        print("_handle_sim_node_message --> " + str(conn.getsockname()))

        def _handle_message(action: bytes, data: List[bytes]) -> bytes:
            if action == b"generateSid":
                result = _generate_sid()
            else:
                message = "The action \"" + action.decode() + "\" is unknown."
                eprint(message)
                result = Void()
                result.message = message
            return result.SerializeToString()

        process_message(conn, _handle_message)


    sim_node_sim_node_com = Thread(target=accept_at_server,
                                   args=(create_server(SIM_NODE_PORT), _handle_sim_node_message))
    sim_node_sim_node_com.daemon = True
    sim_node_sim_node_com.start()


    # Actions to be requested by running simulations
    def _get_vids(sid: SimulationID) -> VehicleIDs:
        vids = VehicleIDs()
        vids.vids.extend([vehicle.vid for vehicle in _get_data(sid).scenario.vehicles.keys()])
        return vids


    def _poll_sensors(sid: SimulationID) -> Void:
        vehicles = _get_data(sid).scenario.vehicles.keys()
        void = Void()
        if _is_simulation_running(sid):
            for vehicle in vehicles:
                _get_data(sid).scenario.bng.poll_sensors(vehicle)
            void.message = "Polled all registered sensors of simulation " + sid.sid + "."
        else:
            void.message = "Skipped polling sensors since simulation " + sid.sid + " is not running anymore."
        return void


    def _verify(sid: SimulationID) -> VerificationResult:
        precondition_fct, failure_fct, success_fct = _get_simulation(sid).get_verification()
        scenario = _get_data(sid).scenario
        precondition = precondition_fct(scenario).eval()
        failure = failure_fct(scenario).eval()
        success = success_fct(scenario).eval()
        verification = VerificationResult()
        verification.precondition = precondition.name
        verification.failure = failure.name
        verification.success = success.name
        return verification


    def _request_ai_for(sid: SimulationID, vid: VehicleID) -> Void:
        print("sim_request_ai_for: enter for " + vid.vid)
        while sid.sid not in _registered_ais \
                or vid.vid not in _registered_ais[sid.sid] \
                or _registered_ais[sid.sid][vid.vid] is not AIStatus.WAITING:
            pass
        _registered_ais[sid.sid][vid.vid] = AIStatus.REQUESTED
        print("sim_request_ai_for: requested for " + vid.vid)
        while _registered_ais[sid.sid][vid.vid] is AIStatus.REQUESTED:
            pass
        print("sim_request_ai_for: leave for " + vid.vid)
        void = Void()
        void.message = "Simulation " + sid.sid + " finished requesting vehicle " + vid.vid + "."
        return void


    def _handle_simulation_message(conn: socket, _: Tuple[str, int]) -> None:
        from common import process_messages
        print("_handle_simulation_message --> " + str(conn.getsockname()))

        def _handle_message(action: bytes, data: List[bytes]) -> bytes:
            if action == b"vids":
                sid = SimulationID()
                sid.ParseFromString(data[0])
                result = _get_vids(sid)
            elif action == b"pollSensors":
                sid = SimulationID()
                sid.ParseFromString(data[0])
                result = _poll_sensors(sid)
            elif action == b"verify":
                sid = SimulationID()
                sid.ParseFromString(data[0])
                result = _verify(sid)
            elif action == b"requestAiFor":
                sid = SimulationID()
                sid.ParseFromString(data[0])
                vid = VehicleID()
                vid.ParseFromString(data[1])
                result = _request_ai_for(sid, vid)
            elif action == b"steps":
                sid = SimulationID()
                sid.ParseFromString(data[0])
                steps = Num()
                steps.ParseFromString(data[1])
                result = Void()
                if _is_simulation_running(sid):
                    _get_data(sid).scenario.bng.step(steps.num)
                    result.message = "Simulated " + str(steps.num) + " steps in simulation " + sid.sid + "."
                else:
                    result.message = "Simulation " + sid.sid + " is not running anymore."
            elif action == b"stop":
                sid = SimulationID()
                sid.ParseFromString(data[0])
                test_result = TestResult()
                test_result.ParseFromString(data[1])
                _control_sim(sid, test_result.result, False)
                result = Void()
            else:
                message = "The action \"" + action.decode() + "\" is unknown."
                eprint(message)
                result = Void()
                result.message = message
            return result.SerializeToString()

        process_messages(conn, _handle_message)


    # Actions to be requested by main application
    def _run_tests(file_content: bytes, user: User) -> MaySimulationIDs:
        from tc_manager import run_tests
        from warnings import warn
        may_sids = MaySimulationIDs()
        try:
            new_tasks = run_tests(file_content)
            if isinstance(new_tasks, Dict):
                if new_tasks:
                    for sim, data in new_tasks.items():
                        if sim.sid.sid in [s.sid.sid for s in _all_tasks.keys()]:
                            warn("The simulation ID " + sim.sid.sid + " already exists and is getting overwritten.")
                            _all_tasks.pop(_get_simulation(sim.sid))
                        may_sids.sids.sids.append(sim.sid.sid)
                        sim.start_server(_handle_simulation_message)
                        data.user = user
                        _all_tasks[sim] = data
                else:
                    may_sids.message.message = "There were no valid tests to run."
            elif isinstance(new_tasks, str):
                may_sids.message.message = new_tasks
            else:
                eprint("Can not handle a _run_tests(...) result of type " + str(type(new_tasks)) + ".")
        except Exception as e:
            eprint("_run_tests(...) errored:")
            eprint(e)
            may_sids.message.message = str(e)
        return may_sids


    def _status(sid: SimulationID) -> SimStateResponse:
        from aiExchangeMessages_pb2 import TestResult
        sim = _get_simulation(sid)
        sim_state = SimStateResponse()
        if sim:
            scenario = _get_data(sid).scenario
            if scenario.bng is None:
                task = _get_data(sid).simulation_task
                if task.get_state() is TestResult.Result.SUCCEEDED \
                        or task.get_state() is TestResult.Result.FAILED:
                    sim_state.state = SimStateResponse.SimState.FINISHED
                elif task.get_state() is TestResult.Result.SKIPPED:
                    sim_state.state = SimStateResponse.SimState.CANCELED
                else:
                    sim_state.state = SimStateResponse.SimState.TIMEOUT
            else:
                sim_state.state = SimStateResponse.SimState.RUNNING
        else:
            sim_state.state = SimStateResponse.SimState.UNKNOWN
        return sim_state


    def _wait_for_simulator_request(sid: SimulationID, vid: VehicleID) -> SimStateResponse:
        print("ai_wait_for_simulator_request: enter for " + vid.vid)
        if sid.sid not in _registered_ais:
            _registered_ais[sid.sid] = {}
        _registered_ais[sid.sid][vid.vid] = AIStatus.WAITING

        while _is_simulation_running(sid) and _registered_ais[sid.sid][vid.vid] is AIStatus.WAITING:
            pass
        response = SimStateResponse()
        data = _get_data(sid)
        scenario = data.scenario
        if scenario.bng is None:
            task = data.simulation_task
            if task.get_state() is TestResult.Result.SUCCEEDED or task.get_state() is TestResult.Result.FAILED:
                response.state = SimStateResponse.SimState.FINISHED
            elif task.get_state() is TestResult.Result.SKIPPED:
                response.state = SimStateResponse.SimState.CANCELED
            elif TestResult.Result.UNKNOWN:
                response.state = SimStateResponse.SimState.TIMEOUT
            else:
                raise NotImplementedError("Handling the TestResult state " + task.state() + " is not implemented, yet.")
        else:
            response.state = SimStateResponse.SimState.RUNNING
        print("ai_wait_for_simulator_request: leave for " + vid.vid)
        return response


    def _control_av(sid: SimulationID, vid: VehicleID, command: Control.AvCommand) -> None:
        """
        :param vid: The vehicle to control.
        :param accelerate: The throttle of the car (Range 0.0 to 1.0)
        :param steer: The steering angle (Range -1.0 to 1.0) # FIXME Negative/Positive left/right?
        :param brake: The brake intensity (Range 0.0 to 1.0)
        """
        vehicle = _get_data(sid).scenario.get_vehicle(vid.vid)
        vehicle.control(throttle=command.accelerate, steering=command.steer, brake=command.brake, parkingbrake=0)


    def store_data(data: SimulationData) -> Any:
        from lxml.etree import tostring
        from aiExchangeMessages_pb2 import TestResult
        result = data.simulation_task.get_state()
        if result is TestResult.Result.SUCCEEDED:
            successful_value = "TRUE"
        elif result is TestResult.Result.FAILED:
            successful_value = "FALSE"
        elif result is TestResult.Result.SKIPPED:
            successful_value = "NULL"
        else:
            eprint("SimulationData can not be stored (data.simulation_task.state() = " + str(result) + ").")
            successful_value = None
        if successful_value:
            args = {
                "environment": tostring(data.environment.getroot()),
                "criteria": tostring(data.criteria),
                "successful": successful_value,
                "started": data.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "finished": data.end_time.strftime("%Y-%m-%d %H:%M:%S"),
                "username": data.user.username
            }
            _dbms_connection.run_query("""
            INSERT INTO tests VALUES
                (DEFAULT, :environment, :criteria, :successful, :started, :finished, :username)
            """, args)
            print(id)
        return None


    def _control_sim(sid: SimulationID, command: int, direct: bool) -> None:
        """
        Stops a simulation and sets its associated test result.
        :param sid: The simulation to stop.
        :param command: The command controlling the simulation or the test result of the simulation to set. (Its "type"
        is Union[Control.SimCommand.Command, TestResult.Result]).
        :param direct: True only if the given command represents a Control.SimCommand.Command controlling the simulation
        directly. False only if the given command represents a TestResult.Result to be associated with the given
        simulation.
        """
        from shutil import rmtree
        from datetime import datetime
        data = _get_data(sid)
        task = data.simulation_task
        if direct:
            if command is Control.SimCommand.Command.SUCCEED:
                task.set_state(TestResult.Result.SUCCEEDED)
            elif command is Control.SimCommand.Command.FAIL:
                task.set_state(TestResult.Result.FAILED)
            elif command is Control.SimCommand.Command.CANCEL:
                task.set_state(TestResult.Result.SKIPPED)
            else:
                raise NotImplementedError("Handling of the SimCommand " + str(command) + " is not implemented, yet.")
        else:
            task.set_state(command)

        data.scenario.bng.close()
        data.end_time = datetime.now()
        store_data(data)

        # Make sure there is no inference with following tests
        sim = _get_simulation(sid)
        rmtree(sim.get_user_path(), ignore_errors=True)


    def _control(sid: SimulationID, vid: VehicleID, control: Control) -> Void:
        print("ai_control: enter for " + vid.vid)
        command_type = control.WhichOneof("command")
        if command_type == "simCommand":
            _control_sim(sid, control.simCommand.command, True)
        elif command_type == "avCommand":
            sim = _get_simulation(sid)
            if sim and sim.get_current_movement_mode(vid.vid) is MovementMode.MANUAL:
                _control_av(sid, vid, control.avCommand)
        else:
            raise NotImplementedError("Interpreting commands of type " + command_type + " is not implemented, yet.")
        print("ai_control: leave for " + vid.vid)
        result = Void()
        result.message = "Controlled vehicle " + vid.vid + " in simulation " + sid.sid + "."
        return result


    def _attach_request_data(data: DataResponse.Data, sid: SimulationID, vid: VehicleID, rid: str) -> None:
        from requests import PositionRequest, SpeedRequest, SteeringAngleRequest, LidarRequest, CameraRequest, \
            DamageRequest, LaneCenterDistanceRequest
        from PIL import Image
        from io import BytesIO
        vehicle = _get_data(sid).scenario.get_vehicle(vid.vid)
        sensor_data = vehicle.poll_request(rid)
        if rid in vehicle.requests:
            request_type = type(vehicle.requests[rid])
            if request_type is PositionRequest:
                data.position.x = sensor_data[0]
                data.position.y = sensor_data[1]
            elif request_type is SpeedRequest:
                data.speed.speed = sensor_data
            elif request_type is SteeringAngleRequest:
                data.angle.angle = sensor_data
            elif request_type is LidarRequest:
                data.lidar.points.extend(sensor_data)
            elif request_type is CameraRequest:
                def _convert(image: Image) -> bytes:
                    bytes_arr = BytesIO()
                    image.save(bytes_arr, format="PNG")
                    return bytes_arr.getvalue()

                data.camera.color = _convert(sensor_data[0])
                data.camera.annotated = _convert(sensor_data[1])
                data.camera.depth = _convert(sensor_data[2])
            elif request_type is DamageRequest:
                data.damage.is_damaged = sensor_data
            elif request_type is LaneCenterDistanceRequest:
                data.lane_center_distance.lane_id = sensor_data[0]
                data.lane_center_distance.distance = sensor_data[1]
            # elif request_type is LightRequest:
            # response = DataResponse.Data.Light()
            # FIXME Add DataResponse.Data.Light
            else:
                raise NotImplementedError(
                    "The conversion from " + str(request_type) + " to DataResponse.Data is not implemented, yet.")
        else:
            raise ValueError("There is no request called \"" + rid + "\".")


    def _request_data(sid: SimulationID, vid: VehicleID, request: DataRequest) -> DataResponse:
        print("ai_request_data: enter for " + vid.vid)
        data_response = DataResponse()
        for rid in request.request_ids:
            try:
                _attach_request_data(data_response.data[rid], sid, vid, rid)
            except ValueError:
                error = DataResponse.Error()
                error.message = "There is no request with ID \"" + rid + "\"."
                data_response[rid] = error
        print("ai_request_data: leave for " + vid.vid)
        return data_response


    def _result(sid: SimulationID) -> TestResult:
        result = TestResult()
        data = _get_data(sid)
        if data:
            state = data.simulation_task.get_state()
            result.result = state if state else TestResult.Result.UNKNOWN
        else:
            result.result = TestResult.Result.UNKNOWN
        return result


    def _get_running_tests(user: User) -> MaySimulationIDs:
        may_sids = MaySimulationIDs()
        for sim, data in _all_tasks.items():
            if _is_simulation_running(sim.sid) and data.user.username == user.username:
                may_sids.sids.sids.append(sim.sid.sid)
        if not may_sids.sids.sids:  # Avoid an empty message
            may_sids.message.message = "No simulations running"
        return may_sids


    def _handle_main_app_message(action: bytes, data: List[bytes]) -> bytes:
        if action == b"runTests":
            user = User()
            user.ParseFromString(data[1])
            result = _run_tests(data[0], user)
        elif action == b"status":
            sid = SimulationID()
            sid.ParseFromString(data[0])
            result = _status(sid)
        elif action == b"waitForSimulatorRequest":
            sid = SimulationID()
            sid.ParseFromString(data[0])
            vid = VehicleID()
            vid.ParseFromString(data[1])
            result = _wait_for_simulator_request(sid, vid)
        elif action == b"control":
            sid = SimulationID()
            sid.ParseFromString(data[0])
            vid = VehicleID()
            vid.ParseFromString(data[1])
            control = Control()
            control.ParseFromString(data[2])
            result = _control(sid, vid, control)
        elif action == b"requestData":
            sid = SimulationID()
            sid.ParseFromString(data[0])
            vid = VehicleID()
            vid.ParseFromString(data[1])
            request = DataRequest()
            request.ParseFromString(data[2])
            result = _request_data(sid, vid, request)
        elif action == b"result":
            sid = SimulationID()
            sid.ParseFromString(data[0])
            result = _result(sid)
        elif action == b"requestSocket":
            client = create_client(MAIN_APP_HOST, MAIN_APP_PORT)
            client_thread = Thread(target=process_messages, args=(client, _handle_main_app_message))
            client_thread.daemon = True
            print("_handle_main_app_message --> " + str(client.getsockname()))
            client_thread.start()
            result = Void()
            result.message = "Connected another client socket to the main app."
        elif action == b"runningTests":
            user = User()
            user.ParseFromString(data[0])
            result = _get_running_tests(user)
        elif action == b"stop":
            sid = SimulationID()
            sid.ParseFromString(data[0])
            test_result = TestResult()
            test_result.ParseFromString(data[1])
            _control_sim(sid, test_result.result, False)
            result = Void()
            result.message = "Stopped simulation " + sid.sid + "."
        else:
            message = "The action \"" + action.decode() + "\" is unknown."
            eprint(message)
            result = Void()
            result.message = message
        return result.SerializeToString()


    main_app_client = create_client(MAIN_APP_HOST, MAIN_APP_PORT)
    snid = SimulationNodeID()
    snid.ParseFromString(main_app_client.recv(1024))  # FIXME Determine appropriate value
    prefix = snid.snid
    if not prefix:
        eprint("SimNode was no prefix assigned.")
        main_app_client.close()
        exit(1)
    sim_node_main_app_com = Thread(target=process_messages, args=(main_app_client, _handle_main_app_message))
    print("_handle_main_app_message --> " + str(main_app_client.getsockname()))
    sim_node_main_app_com.start()
