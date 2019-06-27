from typing import List, Set, Optional, Tuple

from beamngpy import Scenario

from aiExchangeMessages_pb2 import DataResponse
from dbtypes import ExtAsyncResult
from dbtypes.beamng import DBVehicle, DBBeamNGpy
from dbtypes.criteria import TestCase, KPValue
from dbtypes.scheme import Participant, MovementMode
from run_celery import celery
from util import static_vars


class Simulation:

    def __init__(self, sid: str, pickled_test_case: bytes):
        from aiExchangeMessages_pb2 import SimulationID
        sid_obj = SimulationID()
        sid_obj.sid = sid
        self.sid = sid_obj
        self.serialized_sid = sid_obj.SerializeToString()
        self.pickled_test_case = pickled_test_case
        # NOTE Neither BeamNGpy nor Scenario can be serialized

    def _get_movement_mode_file_path(self, pid: str, in_lua: bool) -> str:
        """
        Returns the path of the file for storing the current movement mode of the given participant. The used path separator
        is '/' to allow to be used in lua files.
        :param pid: The participant id to get the path for.
        :param in_lua: Whether the resulting path should be appropriate for lua or python (True=Lua, False=Python).
        :return: The path of the file for storing the movement mode of the given participant.
        """
        from app import app
        import os
        return os.path.join("" if in_lua else app.config["BEAMNG_USER_PATH"],
                            self.sid.sid + "_" + pid + "_movementMode")

    def _get_current_movement_mode(self, pid: str) -> Optional[MovementMode]:
        import os
        mode_file_path = self._get_movement_mode_file_path(pid, False)
        if os.path.exists(mode_file_path):
            mode_file = open(mode_file_path, "r")
            mode = MovementMode[mode_file.readline()]
            mode_file.close()
            return mode
        else:
            return None

    def _generate_lua_av_command(self, participant: Participant, idx: int, next_mode: MovementMode,
                                 current_mode: Optional[MovementMode] = None) -> List[str]:
        """
        NOTE When using this function the lua file where you include this command has to include the following line:
        local sh = require('ge/extensions/scenario/scenariohelper')
        NOTE Pass -1 as idx when passing mode of the initial state of the participant
        """
        lua_av_command = []
        if next_mode is MovementMode.MANUAL:
            # FIXME Recognize speed (limits)
            if current_mode is not MovementMode.MANUAL:
                remaining_waypoints = "{'" + "', '".join(map(lambda w: w.id, participant.movement[idx + 1:])) + "'}"
                lua_av_command.extend([
                    "    sh.setAiRoute('" + participant.id + "', " + remaining_waypoints + ")"
                ])
        else:
            lua_av_command.extend([
                "    sh.setAiMode('" + participant.id + "', 'disabled')"  # Disable previous calls to sh.setAiRoute
            ])
        lua_av_command.extend([
            "    local modeFile = io.open('" + self._get_movement_mode_file_path(participant.id, True) + "', 'w')",
            "    modeFile:write('" + next_mode.value + "')",
            "    modeFile:close()"
        ])
        return lua_av_command

    def _get_lua_path(self) -> str:
        import os
        return os.path.join(
            Simulation._get_scenario_dir_path(),
            self.sid.sid + ".lua"
        )

    @staticmethod
    def _get_scenario_dir_path() -> str:
        from app import app
        import os
        return os.path.join(
            app.config["BEAMNG_USER_PATH"],
            "levels",
            app.config["BEAMNG_LEVEL_NAME"],
            "scenarios"
        )

    def _get_prefab_path(self) -> str:
        import os
        return os.path.join(
            Simulation._get_scenario_dir_path(),
            self.sid.sid + ".prefab"
        )

    def _get_json_path(self) -> str:
        import os
        return os.path.join(
            Simulation._get_scenario_dir_path(),
            self.sid.sid + ".json"
        )

    def _add_to_prefab_file(self, new_content: List[str]) -> None:
        """
        Workaround for adding content to a scenario prefab if there is no explicit method for it.
        :param new_content: The lines of content to add.
        """
        prefab_file_path = self._get_prefab_path()
        prefab_file = open(prefab_file_path, "r")
        original_content = prefab_file.readlines()
        prefab_file.close()
        for line in new_content:
            original_content.insert(-2, line + "\n")
        prefab_file = open(prefab_file_path, "w")
        prefab_file.writelines(original_content)
        prefab_file.close()

    def _add_to_json_file(self, new_content: List[str]) -> None:
        """
        Workaround for adding content to a scenario json if there is no explicit method for it.
        :param new_content: The lines of content to add.
        """
        json_file_path = self._get_json_path()
        json_file = open(json_file_path, "r")
        original_content = json_file.readlines()
        json_file.close()
        original_content[-3] = original_content[-3] + ",\n"  # Make sure previous line has a comma
        for line in new_content:
            original_content.insert(-2, line + "\n")
        json_file = open(json_file_path, "w")
        json_file.writelines(original_content)
        json_file.close()

    def _generate_lua_file(self, participants: List[Participant]) -> None:
        lua_file = open(self._get_lua_path(), "w")
        lua_file.writelines([  # FIXME Is this needed somehow?
            "local M = {}\n",
            "local sh = require('ge/extensions/scenario/scenariohelper')",
            "\n",
            "local function onRaceStart()\n",
        ])
        for participant in participants:
            lua_file.writelines(
                map(lambda l: l + "\r\n",
                    self._generate_lua_av_command(participant, -1, participant.initial_state.mode)))
        lua_file.writelines([
            "end\n",
            "\n",
            "M.onRaceStart = onRaceStart\n",
            "return M"
        ])
        lua_file.close()

    def _add_lua_triggers(self, participants: List[Participant]) -> None:
        for participant in participants:
            current_movement_mode = participant.initial_state.mode
            for idx, waypoint in enumerate(participant.movement[0:-1]):
                x_pos = waypoint.position[0]
                y_pos = waypoint.position[1]
                # NOTE Add further tolerance due to oversize of bounding box of the car compared to the actual body
                tolerance = waypoint.tolerance + 0.5

                def generate_lua_function() -> str:
                    lua_lines = list()
                    lua_lines.extend([
                        "local sh = require('ge/extensions/scenario/scenariohelper')",
                        "local function onWaypoint(data)",
                        "  if data['event'] == 'enter' then"
                    ])
                    lua_lines.extend(
                        self._generate_lua_av_command(participant, idx, waypoint.mode, current_movement_mode))
                    lua_lines.extend([
                        "  end",
                        "end",
                        "",
                        "return onWaypoint"
                    ])
                    return "\\r\\n".join(lua_lines)

                self._add_to_prefab_file([
                    "new BeamNGTrigger() {",
                    "    TriggerType = \"Sphere\";",
                    "    TriggerMode = \"Overlaps\";",
                    "    TriggerTestType = \"Race Corners\";",
                    "    luaFunction = \"" + generate_lua_function() + "\";",
                    "    tickPeriod = \"100\";",  # FIXME Think about it
                    "    debug = \"0\";",
                    "    ticking = \"0\";",  # FIXME Think about it
                    "    triggerColor = \"255 192 0 45\";",
                    "    defaultOnLeave = \"1\";",  # FIXME Think about it
                    "    position = \"" + str(x_pos) + " " + str(y_pos) + " 0.5\";",
                    "    scale = \"" + str(tolerance) + " " + str(tolerance) + " 10\";",
                    "    rotationMatrix = \"1 0 0 0 1 0 0 0 1\";",
                    "    mode = \"Ignore\";",
                    "    canSave = \"1\";",  # FIXME Think about it
                    "    canSaveDynamicFields = \"1\";",  # FIXME Think about it
                    "};"
                ])

                current_movement_mode = waypoint.mode

    def _enable_participant_movements(self, participants: List[Participant]) -> None:
        """
        Adds triggers to the scenario that set the next waypoints for the given participants. Must be called after adding
        the waypoints. Otherwise some IDs of waypoints may be None.
        :param participants: The participants to add movement changing triggers to
        """
        self._generate_lua_file(participants)
        self._add_lua_triggers(participants)

    def _make_lanes_visible(self) -> None:
        """
        Workaround for making lanes visible.
        """
        prefab_file_path = self._get_prefab_path()
        prefab_file = open(prefab_file_path, "r")
        original_content = prefab_file.readlines()
        prefab_file.close()
        new_content = list()
        for line in original_content:
            if "overObjects" in line:
                new_line = line.replace("0", "1")
            else:
                new_line = line
            new_content.append(new_line)
        prefab_file = open(prefab_file_path, "w")
        prefab_file.writelines(new_content)
        prefab_file.close()

    def _request_control_avs(self, vids: List[str]) -> None:
        from util import eprint
        from http.client import HTTPConnection
        from urllib.parse import urlencode
        from aiExchangeMessages_pb2 import VehicleID
        from app import app
        for v in vids:
            mode = self._get_current_movement_mode(v)
            if mode is MovementMode.AUTONOMOUS:
                vid = VehicleID()
                vid.vid = v
                connection = HTTPConnection(host=app.config["MAIN_HOST"], port=app.config["MAIN_PORT"])
                params = urlencode({
                    "sid": self.serialized_sid,
                    "vid": vid.SerializeToString()
                })
                connection.request("GET", "/sim/requestAiFor?" + params)
                connection.getresponse()
                # FIXME Check return status
            elif mode is MovementMode.TRAINING:
                eprint("TRAINING not implemented, yet.")

    def _get_vehicles(self) -> List[DBVehicle]:
        """
        NOTE As long as bng_scenario.make() is not called this will return an empty list.
        """
        import dill as pickle
        return list(
            filter(
                lambda v: v is not None,
                map(
                    lambda vid: self._get_vehicle(vid),
                    [p.id for p in pickle.loads(self.pickled_test_case).scenario.participants]
                )
            )
        )

    def _get_vehicle(self, vid: str) -> DBVehicle:
        """
        NOTE As long as bng_scenario.make() is not called this will return None.
        """
        from app import _get_data
        # FIXME How to avoid this?
        return _get_data(self.sid).scenario.get_vehicle(vid)

    def attach_request_data(self, data: DataResponse.Data, vid: str, rid: str) -> None:
        from requests import PositionRequest, SpeedRequest, SteeringAngleRequest, LidarRequest, CameraRequest, \
            DamageRequest
        from PIL import Image
        from io import BytesIO
        vehicle = self._get_vehicle(vid)
        sensor_data = vehicle.poll_request(rid)
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
        # elif request_type is LightRequest:
        # response = DataResponse.Data.Light()
        # FIXME Add DataResponse.Data.Light
        else:
            raise NotImplementedError(
                "The conversion from " + str(request_type) + " to DataResponse.Data is not implemented, yet.")

    def control_av(self, vid: str, accelerate: float, steer: float, brake: float) -> None:
        """
        :param vid: The vehicle to control.
        :param accelerate: The throttle of the car (Range 0.0 to 1.0)
        :param steer: The steering angle (Range -1.0 to 1.0) # FIXME Negative/Positive left/right?
        :param brake: The brake intensity (Range 0.0 to 1.0)
        """
        # FIXME Check ranges
        vehicle = self._get_vehicle(vid)
        vehicle.control(throttle=accelerate, steering=steer, brake=brake, parkingbrake=0)  # FIXME Seems to be ignored

    def _add_lap_config(self, waypoint_ids: Set[str]) -> None:
        """
        Adds a dummy lapConfig attribute to the scenario json to avoid nil value exceptions.
        """
        if not waypoint_ids == set():
            self._add_to_json_file([
                "        \"lapConfig\": [\"" + ("\", \"".join(waypoint_ids)) + "\"]"
            ])

    def _add_waypoints_to_scenario(self, participants: List[Participant]) -> None:
        """
        This method is only needed until generator.py::add_waypoints_to_scenario can be implemented.
        NOTE: This method has to be called after scenario.make()
        """
        for participant in participants:
            wp_prefix = "wp_" + participant.id + "_"
            counter = 0
            for waypoint in participant.movement:
                if waypoint.id is None:
                    waypoint.id = wp_prefix + str(counter)
                    counter += 1
                tolerance = str(waypoint.tolerance)
                self._add_to_prefab_file([
                    "new BeamNGWaypoint(" + waypoint.id + "){",
                    "   drawDebug = \"0\";",
                    "   directionalWaypoint = \"0\";",  # FIXME Should I use directional waypoints?
                    "   position = \"" + str(waypoint.position[0]) + " " + str(waypoint.position[1]) + " 0\";",
                    "   scale = \"" + tolerance + " " + tolerance + " " + tolerance + "\";",
                    "   rotationMatrix = \"1 0 0 0 1 0 0 0 1\";",
                    "   mode = \"Ignore\";",  # FIXME Which mode is suitable?
                    "   canSave = \"1\";",  # FIXME Think about it
                    "   canSaveDynamicFields = \"1\";",  # FIXME Think about it
                    "};"
                ])

    @staticmethod
    def _is_port_available(port: int) -> bool:
        from socket import socket, AF_INET, SOCK_STREAM
        sock = socket(AF_INET, SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        is_open = (result != 0)
        sock.close()
        return is_open

    def verify(self) -> Tuple[KPValue, KPValue, KPValue]:
        """
        The type may be either precondition, failure or success.
        """
        import dill as pickle
        from app import _get_data
        test_case: TestCase = pickle.loads(self.pickled_test_case)
        bng_scenario = _get_data(self.sid).scenario
        return test_case.precondition_fct(bng_scenario).eval(), \
               test_case.failure_fct(bng_scenario).eval(), \
               test_case.success_fct(bng_scenario).eval()

    @celery.task
    def _run_runtime_verification(self, ai_frequency: int) -> None:
        """
        NOTE Since this method is a celery task it must not call anything that depends on a Scenario neither directly
        nor indirectly.
        """
        # FIXME How to avoid all these requests?!
        from httpUtil import do_get_request
        from app import app
        from aiExchangeMessages_pb2 import VehicleID, VehicleIDs, TestResult

        def _get_verification() -> Tuple[KPValue, KPValue, KPValue]:
            from aiExchangeMessages_pb2 import VerificationResult
            response = do_get_request("localhost", app.config["PORT"], "/sim/verify", {"sid": self.serialized_sid})
            verification = VerificationResult()
            verification.ParseFromString(b"".join(response.readlines()))
            return KPValue[verification.precondition], KPValue[verification.failure], KPValue[verification.success]

        test_case_result: Optional[TestResult.Result] = None
        vidsResult = do_get_request("localhost", app.config["PORT"], "/sim/vids", {"sid": self.serialized_sid})
        vids = VehicleIDs()
        vids.ParseFromString(b"".join(vidsResult.readlines()))
        while test_case_result is None:
            for v in vids.vids:
                vid = VehicleID()
                vid.vid = v
                do_get_request("localhost", app.config["PORT"], "/sim/pollSensors", {
                    "sid": self.serialized_sid,
                    "vid": vid.SerializeToString()
                })
            precondition, failure, success = _get_verification()
            if precondition is KPValue.FALSE:
                test_case_result = TestResult.Result.SKIPPED
            elif failure is KPValue.TRUE:
                test_case_result = TestResult.Result.FAILED
            elif success is KPValue.TRUE:
                test_case_result = TestResult.Result.SUCCEEDED
            else:
                self._request_control_avs(vids.vids)
                do_get_request("localhost", app.config["PORT"], "/sim/steps", {
                    "sid": self.serialized_sid,
                    "steps": ai_frequency
                })
        result = TestResult()
        result.result = test_case_result
        do_get_request("localhost", app.config["PORT"], "/sim/stop", {
            "sid": self.serialized_sid,
            "result": result.SerializeToString()
        })

    @static_vars(port=64256)
    def _start_simulation(self, test_case: TestCase) -> Tuple[Scenario, ExtAsyncResult]:
        from app import app
        import os
        from shutil import rmtree
        from redis import Redis

        home_path = app.config["BEAMNG_INSTALL_FOLDER"]
        user_path = app.config["BEAMNG_USER_PATH"]

        # Make sure there is no inference with previous tests while keeping the cache
        rmtree(os.path.join(user_path, "levels", app.config["BEAMNG_LEVEL_NAME"], self.sid.sid + ".*"),
               ignore_errors=True)

        with Redis().lock("beamng_start_lock"):
            while not Simulation._is_port_available(Simulation._start_simulation.port):
                Simulation._start_simulation.port += 100  # Make sure to not interfere with previously started simulations
            bng_instance = DBBeamNGpy('localhost', Simulation._start_simulation.port, home=home_path, user=user_path)
            authors = ", ".join(test_case.authors)
            bng_scenario = Scenario(app.config["BEAMNG_LEVEL_NAME"], self.sid.sid, authors=authors)

            test_case.scenario.add_all(bng_scenario)
            bng_scenario.make(bng_instance)

            # Make manual changes to the scenario files
            self._make_lanes_visible()
            self._add_waypoints_to_scenario(test_case.scenario.participants)
            self._enable_participant_movements(test_case.scenario.participants)
            waypoints = set()
            for wps in [p.movement for p in test_case.scenario.participants]:
                for wp in wps:
                    if wp.id is not None:  # FIXME Not all waypoints are added
                        waypoints.add(wp.id)
            self._add_lap_config(waypoints)  # NOTE This call just solves an error showing up in the console of BeamNG

            bng_instance.open(launch=True)
            bng_instance.load_scenario(bng_scenario)
            bng_instance.set_steps_per_second(test_case.stepsPerSecond)
            bng_instance.set_deterministic()
            bng_instance.hide_hud()
            bng_instance.start_scenario()
            bng_instance.pause()

        return bng_scenario, ExtAsyncResult(Simulation._run_runtime_verification.delay(self, test_case.aiFrequency))


def run_test_case(test_case: TestCase) -> Tuple[Simulation, Scenario, ExtAsyncResult]:
    """
    This method starts the actual simulation in a separate thread.
    Additionally it already calculates and attaches all information that is need by this node and the separate
    thread before calling _start_simulation(...).
    """
    import dill as pickle
    from random import randint
    from app import _get_simulation
    from aiExchangeMessages_pb2 import SimulationID
    while True:  # Pseudo "do-while"-loop
        sid = "sim_" + str(randint(0, 10000))
        sid_obj = SimulationID()
        sid_obj.sid = sid
        if _get_simulation(sid_obj) is None:
            break
    sim = Simulation(sid, pickle.dumps(test_case))
    bng_scenario, task = sim._start_simulation(test_case)

    return sim, bng_scenario, task
