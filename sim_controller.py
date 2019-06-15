from typing import List, Set, Optional

from beamngpy import Scenario

from aiExchangeMessages_pb2 import DataResponse
from dbtypes.criteria import TestCase
from dbtypes.scheme import Participant, MovementMode
from util import static_vars


class Simulation:
    running_simulations = []

    def __init__(self, sid: str):
        self.sid = sid
        self.vehicles = []

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
        return os.path.join("" if in_lua else app.config["BEAMNG_USER_PATH"], self.sid + "_" + pid + "_movementMode")

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
                "    sh.setAiMode('" + participant.id + "', 'MANUAL')"  # Disable previous calls to sh.setAiRoute
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
            self.sid + ".lua"
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
            self.sid + ".prefab"
        )

    def _get_json_path(self) -> str:
        import os
        return os.path.join(
            Simulation._get_scenario_dir_path(),
            self.sid + ".json"
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

    def _control_avs(self) -> None:
        from util import eprint
        from communicator import sim_request_ai_for
        from aiExchangeMessages_pb2 import AiID
        for vehicle in self.vehicles:
            mode = self._get_current_movement_mode(vehicle.vid)
            if mode is MovementMode.AUTONOMOUS:
                aid = AiID()
                aid.vid.vid = vehicle.vid
                aid.sid.sid = self.sid
                sim_request_ai_for(aid)
            elif mode is MovementMode.TRAINING:
                eprint("TRAINING not implemented, yet.")

    def _get_vehicle(self, vid: str):
        found_vehicles = list(filter(lambda v: v.vid == vid, self.vehicles))
        if found_vehicles:
            return found_vehicles[0]
        else:
            raise ValueError("The simulation " + self.sid + " contains no vehicle " + vid + ".")

    def attach_request_data(self, data: DataResponse.Data, vid: str, rid: str) -> None:
        from requests import PositionRequest, SpeedRequest, SteeringAngleRequest, LidarRequest, CameraRequest, \
            DamageRequest, LightRequest
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

    @staticmethod
    @static_vars(port=64256)
    def run_test_case(test_case: TestCase):
        from app import app
        from dbtypes.beamng import DBBeamNGpy
        from dbtypes.criteria import KPValue
        from shutil import rmtree
        import os
        home_path = app.config["BEAMNG_INSTALL_FOLDER"]
        user_path = app.config["BEAMNG_USER_PATH"]

        # Make sure there is no inference with previous tests while keeping the cache
        rmtree(os.path.join(user_path, "levels"), ignore_errors=True)

        # FIXME Generate sids automatically
        sim = Simulation("fancySid")
        Simulation.running_simulations.append(sim)
        while not Simulation._is_port_available(Simulation.run_test_case.port):
            Simulation.run_test_case.port += 1
        bng_instance = DBBeamNGpy('localhost', Simulation.run_test_case.port, home=home_path, user=user_path)
        authors = ", ".join(test_case.authors)
        bng_scenario = Scenario(app.config["BEAMNG_LEVEL_NAME"], sim.sid, authors=authors)

        test_case.scenario.add_all(bng_scenario)
        vehicles = [bng_scenario.get_vehicle(participant.id) for participant in test_case.scenario.participants]
        sim.vehicles = vehicles
        bng_scenario.make(bng_instance)

        # Make manual changes to the scenario files
        sim._make_lanes_visible()
        sim._add_waypoints_to_scenario(test_case.scenario.participants)
        sim._enable_participant_movements(test_case.scenario.participants)
        waypoints = set()
        for wps in [p.movement for p in test_case.scenario.participants]:
            for wp in wps:
                if wp.id is not None:  # FIXME Not all waypoints are added
                    waypoints.add(wp.id)
        sim._add_lap_config(waypoints)  # NOTE This call just solves an error showing up in the console of BeamNG

        bng_instance.open(launch=True)
        try:
            bng_instance.load_scenario(bng_scenario)
            bng_instance.set_steps_per_second(test_case.stepsPerSecond)
            bng_instance.set_deterministic()
            bng_instance.hide_hud()
            bng_instance.start_scenario()
            bng_instance.pause()

            precondition = test_case.precondition_fct(bng_scenario)
            failure = test_case.failure_fct(bng_scenario)
            success = test_case.success_fct(bng_scenario)
            test_case_result = "undetermined"
            input("Press \"Enter\" for starting the simulation...")
            while test_case_result == "undetermined":
                # input("Press \"Enter\" for running another runtime verification cycle...")
                for vehicle in sim.vehicles:
                    bng_instance.poll_sensors(vehicle)
                if precondition.eval() is KPValue.FALSE:
                    test_case_result = "skipped"
                elif failure.eval() is KPValue.TRUE:
                    test_case_result = "failed"
                elif success.eval() is KPValue.TRUE:
                    test_case_result = "succeeded"
                else:
                    # test_case_result = "undetermined"
                    sim._control_avs()
                    bng_instance.step(test_case.aiFrequency)
            print("Test case result: " + test_case_result)
        finally:
            bng_instance.close()
            Simulation.running_simulations.remove(sim)
