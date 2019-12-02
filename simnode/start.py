import copyreg
from datetime import datetime
from logging import getLogger, basicConfig, INFO
from socket import socket
from threading import Thread, Lock
from typing import Dict, Optional, Tuple, List

from drivebuildclient import accept_at_server, create_server, create_client, process_requests
from drivebuildclient.aiExchangeMessages_pb2 import SimulationID, VehicleIDs, Void, VerificationResult, VehicleID, Num, \
    TestResult, SubmissionResult, User, SimStateResponse, Control, DataResponse, DataRequest, SimulationNodeID
from drivebuildclient.db_handler import DBConnection
from lxml.etree import _Element

from config import SIM_NODE_PORT, MAIN_APP_HOST, MAIN_APP_PORT, DBMS_HOST, DBMS_PORT, DBMS_DBNAME, DBMS_USERNAME, \
    DBMS_PASSWORD
from dbtypes import SimulationData
from dbtypes.scheme import MovementMode
from sim_controller import Simulation

_DB_CONNECTION = DBConnection(DBMS_HOST, DBMS_PORT, DBMS_DBNAME, DBMS_USERNAME, DBMS_PASSWORD)
_logger = getLogger("DriveBuild.SimNode.Start")


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
    _all_tasks: Dict[Simulation, SimulationData] = {}
    # sid --> (vid --> (numSimReady, numAiReady))
    _registered_ais: Dict[str, Dict[str, Tuple[int, int]]] = {}
    _registered_ais_lock = Lock()
    basicConfig(format='%(asctime)s: %(levelname)s - %(message)s', level=INFO)


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
        sid_cursor = _DB_CONNECTION.run_query("""
        INSERT INTO tests VALUES (DEFAULT, NULL, NULL, NULL, NULL, NULL, NULL, NULL) RETURNING sid;
        """)
        if sid_cursor:
            result = sid_cursor.fetchall()
            sid = SimulationID()
            sid.sid = str(result[0][0])
            return sid
        else:
            _logger.error("Generation of sid failed.")


    def _handle_sim_node_message(conn: socket, _: Tuple[str, int]) -> None:
        from drivebuildclient import process_request
        _logger.debug("_handle_sim_node_message --> " + str(conn.getsockname()))

        def _handle_message(action: bytes, data: List[bytes]) -> bytes:
            if action == b"generateSid":
                result = _generate_sid()
            else:
                message = "The action \"" + action.decode() + "\" is unknown."
                _logger.info(message)
                result = Void()
                result.message = message
            return result.SerializeToString()

        process_request(conn, _handle_message)


    sim_node_sim_node_com = Thread(target=accept_at_server,
                                   args=(create_server(SIM_NODE_PORT), _handle_sim_node_message))
    sim_node_sim_node_com.daemon = True
    sim_node_sim_node_com.start()


    # Actions to be requested by running simulations
    def _get_vids(sid: SimulationID) -> VehicleIDs:
        vids = VehicleIDs()
        vids.vids.extend([vehicle.vid for vehicle in _get_data(sid).scenario.vehicles.keys()])
        return vids


    def _time_to_string(time: datetime) -> str:
        return time.strftime("%Y-%m-%d %H:%M:%S")


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
        from dbtypes.criteria import KPValue
        verification = VerificationResult()
        if _is_simulation_running(sid):
            precondition_fct, failure_fct, success_fct = _get_simulation(sid).get_verification()
            scenario = _get_data(sid).scenario
            precondition = precondition_fct(scenario).eval()
            failure = failure_fct(scenario).eval()
            success = success_fct(scenario).eval()
            verification.precondition = precondition.name
            verification.failure = failure.name
            verification.success = success.name
        else:
            verification.precondition = verification.failure = verification.success = KPValue.UNKNOWN.name
        return verification


    def _init_registered_ais(sid: SimulationID, vid: VehicleID) -> None:
        if sid.sid not in _registered_ais:
            _registered_ais[sid.sid] = {}
        if vid.vid not in _registered_ais[sid.sid]:
            _registered_ais[sid.sid][vid.vid] = (0, 0)


    def _request_ai_for(sid: SimulationID, vid: VehicleID) -> Void:
        from time import sleep
        _logger.debug("sim_request_ai_for: enter for " + sid.sid + ":" + vid.vid)
        _registered_ais_lock.acquire()
        _init_registered_ais(sid, vid)
        num_sim_ready, num_ai_ready = _registered_ais[sid.sid][vid.vid]
        _registered_ais[sid.sid][vid.vid] = (num_sim_ready + 1, num_ai_ready)
        _logger.debug(sid.sid + ":" + vid.vid + " after raf: " + str(_registered_ais[sid.sid][vid.vid]))
        _registered_ais_lock.release()
        while _registered_ais[sid.sid][vid.vid][1] < _registered_ais[sid.sid][vid.vid][0] \
                and _is_simulation_running(sid):
            _logger.debug(sid.sid + ":" + vid.vid + " wait for ai ready")
            sleep(5)
            pass  # Wait for all being ready
        _logger.debug("sim_request_ai_for: leave for " + sid.sid + ":" + vid.vid)
        void = Void()
        void.message = "Simulation " + sid.sid + " finished requesting vehicle " + vid.vid + "."
        return void


    def _store_verification_cycle(sid: SimulationID, started: datetime, finished: datetime) -> Void:
        vehicles = _get_data(sid).scenario.vehicles.keys()
        void = Void()
        if _is_simulation_running(sid):
            for vehicle in vehicles:
                vid = VehicleID()
                vid.vid = vehicle.vid
                request = DataRequest()
                request.request_ids.extend(vehicle.requests)
                data = _request_data(sid, vid, request)
                args = {
                    "sid": sid.sid,
                    "vid": vid.vid,
                    "tick": _get_data(sid).scenario.bng.current_tick,
                    "data": data.SerializeToString(),
                    "started": _time_to_string(started),
                    "finished": _time_to_string(finished)
                }
                _DB_CONNECTION.run_query("""
                INSERT INTO verificationcycles VALUES
                (:sid, :vid, :tick, :data, :started, :finished);
                """, args)
            void.message = "Stored data of the current runtime verification cycle of simulation " + sid.sid + "."
        else:
            void.message = "Skipped storing the data of the current runtime verification cycle since simulation " \
                           + sid.sid + " does not run anymore."
        return void


    def _handle_simulation_message(conn: socket, _: Tuple[str, int]) -> None:
        from drivebuildclient import process_requests
        _logger.info("_handle_simulation_message --> " + str(conn.getsockname()))

        def _handle_message(action: bytes, data: List[bytes]) -> bytes:
            from drivebuildclient.aiExchangeMessages_pb2 import Bool
            if action == b"isRunning":
                sid = SimulationID()
                sid.ParseFromString(data[0])
                result = Bool()
                result.value = _is_simulation_running(sid)
            elif action == b"vids":
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
            elif action == b"storeVerificationCycle":
                sid = SimulationID()
                sid.ParseFromString(data[0])
                started = Num()
                started.ParseFromString(data[1])
                finished = Num()
                finished.ParseFromString(data[2])
                result = _store_verification_cycle(sid, datetime.fromtimestamp(started.num),
                                                   datetime.fromtimestamp(finished.num))
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
                _logger.info(message)
                result = Void()
                result.message = message
            return result.SerializeToString()

        process_requests(conn, _handle_message)


    def _status(sid: SimulationID) -> SimStateResponse:
        sim = _get_simulation(sid)
        sim_state = SimStateResponse()
        if sim:
            scenario = _get_data(sid).scenario
            if scenario.bng is None:
                # FIXME Detect simulations with enforced result (Manually stopped)
                task = _get_data(sid).simulation_task
                if task.get_state() is TestResult.Result.SUCCEEDED \
                        or task.get_state() is TestResult.Result.FAILED:
                    sim_state.state = SimStateResponse.SimState.FINISHED
                elif task.get_state() is TestResult.Result.SKIPPED:
                    # NOTE Skipped => stopped, canceled or unfulfilled precondition
                    sim_state.state = SimStateResponse.SimState.CANCELED
                else:
                    # FIXME Manually stopped with enforced result UNKNOWN => Classified as TIMEOUT
                    sim_state.state = SimStateResponse.SimState.TIMEOUT
            else:
                sim_state.state = SimStateResponse.SimState.RUNNING
        else:
            sim_state.state = SimStateResponse.SimState.UNKNOWN
        return sim_state


    def _result(sid: SimulationID) -> TestResult:
        result = TestResult()
        data = _get_data(sid)
        if data:
            state = data.simulation_task.get_state()
            result.result = state if state else TestResult.Result.UNKNOWN
        else:
            result.result = TestResult.Result.UNKNOWN
        return result


    def _update_test_data(data: SimulationData) -> None:
        from lxml.etree import tostring
        args = {
            "environment": tostring(data.environment) if data.environment else None,
            "criteria": tostring(data.criteria) if data.criteria else None,
            "result": TestResult.Result.Name(_result(data.sid).result),
            "status": SimStateResponse.SimState.Name(_status(data.sid).state),
            "started": data.start_time.strftime("%Y-%m-%d %H:%M:%S") if data.start_time else None,
            "finished": data.end_time.strftime("%Y-%m-%d %H:%M:%S") if data.end_time else None,
            "username": data.user.username if data.user else None,
            "sid": int(data.sid.sid)
        }
        _DB_CONNECTION.run_query("""
        UPDATE tests
        SET "environment" = :environment,
            "criteria" = :criteria,
            "result" = :result,
            "status" = :status,
            "started" = :started,
            "finished" = :finished,
            "username" = :username
        WHERE "sid" = :sid;
        """, args)


    # Actions to be requested by main application
    def _run_tests(file_content: bytes, user: User) -> SubmissionResult:
        from tc_manager import run_tests
        from warnings import warn
        submission_result = SubmissionResult()
        try:
            new_tasks = run_tests(file_content)
            if isinstance(new_tasks, Dict):
                if new_tasks:
                    for sim, data in new_tasks.items():
                        if sim.sid.sid in [s.sid.sid for s in _all_tasks.keys()]:
                            warn("The simulation ID " + sim.sid.sid + " already exists and is getting overwritten.")
                            _all_tasks.pop(_get_simulation(sim.sid))
                        submission_result.result.submissions[sim.test_name].sid = sim.sid.sid
                        sim.start_server(_handle_simulation_message)
                        data.user = user
                        _all_tasks[sim] = data
                        _update_test_data(data)
                else:
                    submission_result.message.message = "There were no valid tests to run."
            elif isinstance(new_tasks, str):
                submission_result.message.message = new_tasks
            else:
                _logger.warning("Can not handle a _run_tests(...) result of type " + str(type(new_tasks)) + ".")
        except Exception as e:
            _logger.exception("Running submitted tests failed")
            submission_result.message.message = str(e)
        return submission_result


    def _wait_for_simulator_request(sid: SimulationID, vid: VehicleID) -> SimStateResponse:
        from time import sleep
        _logger.info("_wait_for_simulator_request: enter for " + sid.sid + ":" + vid.vid)
        _registered_ais_lock.acquire()
        _init_registered_ais(sid, vid)
        num_sim_ready, num_ai_ready = _registered_ais[sid.sid][vid.vid]
        _registered_ais[sid.sid][vid.vid] = (num_sim_ready, num_ai_ready + 1)
        _registered_ais_lock.release()
        while _registered_ais[sid.sid][vid.vid][0] < _registered_ais[sid.sid][vid.vid][1] \
                and _is_simulation_running(sid):
            sleep(5)
            pass  # Wait all being ready
        response = _status(sid)
        _logger.info("_wait_for_simulator_request: leave for " + sid.sid + ":" + vid.vid)
        return response


    def _control_av(sid: SimulationID, vid: VehicleID, command: Control.AvCommand) -> None:
        """
        :param vid: The vehicle to control.
        :param accelerate: The throttle of the car (Range 0.0 to 1.0)
        :param steer: The steering angle (Range -1.0 to 1.0) # FIXME Negative/Positive left/right?
        :param brake: The brake intensity (Range 0.0 to 1.0)
        """
        vehicle = _get_data(sid).scenario.get_vehicle(vid.vid)
        try:
            vehicle.control(throttle=command.accelerate, steering=command.steer, brake=command.brake, parkingbrake=0)
        except Exception:
            _logger.exception("Controlling a vehicle failed.")


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

        if _is_simulation_running(sid):
            data.scenario.bng.close()
        data.end_time = datetime.now()
        _update_test_data(data)


    def _control(sid: SimulationID, vid: VehicleID, control: Control) -> Void:
        _logger.info("ai_control: enter for " + vid.vid)
        result = Void()
        if _is_simulation_running(sid):
            command_type = control.WhichOneof("command")
            if command_type == "simCommand":
                _control_sim(sid, control.simCommand.command, True)
            elif command_type == "avCommand":
                sim = _get_simulation(sid)
                if sim and sim.get_current_movement_mode(vid.vid) is MovementMode.AUTONOMOUS:
                    _control_av(sid, vid, control.avCommand)
            else:
                raise NotImplementedError("Interpreting commands of type " + command_type + " is not implemented, yet.")
            result.message = "Controlled vehicle " + vid.vid + " in simulation " + sid.sid + "."
        else:
            result.message = "Simulation " + sid.sid + " does not run."
        _logger.info("ai_control: leave for " + vid.vid)
        return result


    def _attach_request_data(data: DataResponse.Data, sid: SimulationID, vid: VehicleID, rid: str) -> None:
        from requests import PositionRequest, SpeedRequest, SteeringAngleRequest, LidarRequest, CameraRequest, \
            DamageRequest, RoadCenterDistanceRequest, CarToLaneAngleRequest, BoundingBoxRequest, RoadEdgesRequest
        from PIL import Image
        from io import BytesIO
        from shapely.geometry import mapping
        vehicle = _get_data(sid).scenario.get_vehicle(vid.vid)
        if rid in vehicle.requests:
            sensor_data = vehicle.poll_request(rid, _get_data(sid).scenario)
            if sensor_data:
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
                        bytes_arr.seek(0)
                        return bytes_arr.read()

                    data.camera.color = _convert(sensor_data[0])
                    data.camera.annotated = _convert(sensor_data[1])
                    data.camera.depth = _convert(sensor_data[2])
                elif request_type is DamageRequest:
                    data.damage.is_damaged = sensor_data
                elif request_type is RoadCenterDistanceRequest:
                    data.road_center_distance.road_id = sensor_data[0]
                    data.road_center_distance.distance = sensor_data[1]
                elif request_type is CarToLaneAngleRequest:
                    data.car_to_lane_angle.lane_id = sensor_data[0]
                    data.car_to_lane_angle.angle = float(sensor_data[1])
                elif request_type is BoundingBoxRequest:
                    points = mapping(sensor_data)["coordinates"][0]
                    for point in points:
                        data.bounding_box.points.append(point[0])
                        data.bounding_box.points.append(point[1])
                elif request_type is RoadEdgesRequest:
                    for rid, (left_points, right_points) in sensor_data.items():
                        data.road_edges.edges[rid].left_points.extend([e for p in left_points for e in p])
                        data.road_edges.edges[rid].right_points.extend([e for p in right_points for e in p])
                # elif request_type is LightRequest:
                # response = DataResponse.Data.Light()
                # FIXME Add DataResponse.Data.Light
                else:
                    raise NotImplementedError(
                        "The conversion from " + str(request_type) + " to DataResponse.Data is not implemented, yet.")
            else:
                _logger.warning("Could not attach data for request \"" + rid
                                + "\" of vehicle \"" + vid.vid
                                + "\" in simulation \"" + str(sid.sid) + "\".")
        else:
            raise ValueError("There is no request called \"" + rid + "\".")


    def _request_data(sid: SimulationID, vid: VehicleID, request: DataRequest) -> DataResponse:
        data_response = DataResponse()
        for rid in request.request_ids:
            try:
                if _is_simulation_running(sid):
                    _attach_request_data(data_response.data[rid], sid, vid, rid)
                else:
                    data_response.data[rid].error.message = "The simulation does not run anymore."
            except ValueError:
                data_response.data[rid].error.message = "There is no request with ID \"" + rid + "\"."
        return data_response


    def _get_running_tests(user: User) -> SubmissionResult:
        submission_result = SubmissionResult()
        for sim, data in _all_tasks.items():
            if _is_simulation_running(sim.sid) and data.user.username == user.username:
                submission_result.result.submissions[sim.test_name].sid = sim.sid.sid
        if not submission_result.result.submissions:  # Avoid an empty message
            submission_result.message.message = "No simulations running"
        return submission_result


    def _handle_main_app_message(action: bytes, data: List[bytes]) -> bytes:
        from google.protobuf.message import DecodeError
        if action == b"runTests":
            user = User()
            try:
                user.ParseFromString(data[1])
                result = _run_tests(data[0], user)
            except DecodeError:
                _logger.exception("Running a test failed since \"" + str(data[1]) + "\" can not be parsed to an User")
                result = SubmissionResult()
                result.message.message = "The user parameter could not be parsed."
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
        elif action == b"requestSocket":
            client = create_client(MAIN_APP_HOST, MAIN_APP_PORT)
            client_thread = Thread(target=process_requests, args=(client, _handle_main_app_message))
            client_thread.daemon = True
            _logger.info("_handle_main_app_message --> " + str(client.getsockname()))
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
            _logger.info(message)
            result = Void()
            result.message = message
        return result.SerializeToString()


    main_app_client = create_client(MAIN_APP_HOST, MAIN_APP_PORT)
    snid = SimulationNodeID()
    snid.ParseFromString(main_app_client.recv(1024))  # FIXME Determine appropriate value
    prefix = snid.snid
    if not prefix:
        _logger.error("SimNode was no prefix assigned.")
        main_app_client.close()
        exit(1)
    sim_node_main_app_com = Thread(target=process_requests, args=(main_app_client, _handle_main_app_message))
    _logger.info("_handle_main_app_message --> " + str(main_app_client.getsockname()))
    sim_node_main_app_com.start()
