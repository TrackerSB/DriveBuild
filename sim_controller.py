from socket import socket
from threading import Lock
from typing import List, Set, Optional, Tuple, Callable

from beamngpy import Scenario

from aiExchangeMessages_pb2 import SimulationID
from dbtypes import ExtThread
from dbtypes.beamng import DBBeamNGpy
from dbtypes.criteria import TestCase, KPValue, CriteriaFunction
from dbtypes.scheme import Participant, MovementMode
from util import static_vars


class Simulation:
    def __init__(self, sid: SimulationID, pickled_test_case: bytes, port: int):
        self.sid = sid
        self.serialized_sid = sid.SerializeToString()
        self.pickled_test_case = pickled_test_case
        self.port = port
        self._sim_server_socket = None
        self._sim_node_client_socket = None

    def start_server(self, handle_simulation_message: Callable[[socket, Tuple[str, int]], None]) -> None:
        from threading import Thread
        from common import accept_at_server, create_server
        if self._sim_server_socket:
            raise ValueError("The simulation already started a server at " + str(self.port))
        else:
            self._sim_server_socket = create_server(self.port)
            simulation_sim_node_com_server = Thread(target=accept_at_server,
                                                    args=(self._sim_server_socket, handle_simulation_message))
            simulation_sim_node_com_server.daemon = True
            simulation_sim_node_com_server.start()

    def send_message_to_sim_node(self, action: bytes, data: List[bytes], timeout: Optional[float] = None) -> bytes:
        from common import send_message, create_client
        if not self._sim_node_client_socket:
            self._sim_node_client_socket = create_client("localhost", self.port)
        return send_message(self._sim_node_client_socket, action, data, timeout)

    def _get_movement_mode_file_path(self, pid: str, in_lua: bool) -> str:
        """
        Returns the path of the file for storing the current movement mode of the given participant. The used path separator
        is '/' to allow to be used in lua files.
        :param pid: The participant id to get the path for.
        :param in_lua: Whether the resulting path should be appropriate for lua or python (True=Lua, False=Python).
        :return: The path of the file for storing the movement mode of the given participant.
        """
        import os
        return os.path.join("" if in_lua else self.get_user_path(), pid + "_movementMode")

    def get_current_movement_mode(self, pid: str) -> Optional[MovementMode]:
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
        if next_mode in [MovementMode.MANUAL, MovementMode.TRAINING]:
            # FIXME Recognize speed (limits)
            if current_mode not in [MovementMode.MANUAL, MovementMode.TRAINING]:
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

    def get_user_path(self) -> str:
        from config import BEAMNG_USER_PATH
        import os
        return os.path.join(BEAMNG_USER_PATH, self.sid.sid)

    def _get_lua_path(self) -> str:
        import os
        return os.path.join(
            self._get_scenario_dir_path(),
            self.sid.sid + ".lua"
        )

    def _get_scenario_dir_path(self) -> str:
        from config import BEAMNG_LEVEL_NAME
        import os
        return os.path.join(
            self.get_user_path(),
            "levels",
            BEAMNG_LEVEL_NAME,
            "scenarios"
        )

    def _get_prefab_path(self) -> str:
        import os
        return os.path.join(
            self._get_scenario_dir_path(),
            self.sid.sid + ".prefab"
        )

    def _get_json_path(self) -> str:
        import os
        return os.path.join(
            self._get_scenario_dir_path(),
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
        from common import eprint
        from aiExchangeMessages_pb2 import VehicleID
        for v in vids:
            mode = self.get_current_movement_mode(v)
            if mode in [MovementMode.AUTONOMOUS, MovementMode.TRAINING]:
                vid = VehicleID()
                vid.vid = v
                # FIXME Determine appropriate timeout
                message = self.send_message_to_sim_node(b"requestAiFor", [self.serialized_sid, vid.SerializeToString()])
                print(message)
                # FIXME Continue...
            elif not mode:
                eprint("There is current MovementMode set.")

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

    def get_verification(self) -> Tuple[CriteriaFunction, CriteriaFunction, CriteriaFunction]:
        """
        Returns precondition, failure and success function.
        """
        import dill as pickle
        test_case: TestCase = pickle.loads(self.pickled_test_case)
        return test_case.precondition_fct, test_case.failure_fct, test_case.success_fct

    def _run_runtime_verification(self, ai_frequency: int) -> None:
        """
        NOTE Since this method is a celery task it must not call anything that depends on a Scenario neither directly
        nor indirectly.
        """
        # FIXME Update the previous note to match threading instead of celery
        from aiExchangeMessages_pb2 import TestResult, VehicleIDs, Num

        def _get_verification() -> Tuple[KPValue, KPValue, KPValue]:
            from aiExchangeMessages_pb2 import VerificationResult
            from common import eprint
            # FIXME Determine appropriate timeout
            response = self.send_message_to_sim_node(b"verify", [self.serialized_sid], 10)
            if response:
                verification = VerificationResult()
                verification.ParseFromString(response)
                return KPValue[verification.precondition], KPValue[verification.failure], KPValue[verification.success]
            else:
                eprint("Verification of criteria at simulation " + self.sid.sid + " timed out.")
                return KPValue.UNKNOWN, KPValue.UNKNOWN, KPValue.UNKNOWN

        # FIXME Wait for simulation to be registered at the simulation node?
        # FIXME Use is_simulation_running?
        response = self.send_message_to_sim_node(b"vids", [self.serialized_sid])
        vids = VehicleIDs()
        vids.ParseFromString(response)
        print("vids: " + str(vids.vids))
        test_case_result: Optional[TestResult.Result] = None
        while test_case_result is None:
            self.send_message_to_sim_node(b"pollSensors", [self.serialized_sid])
            print("Polled sensors")
            precondition, failure, success = _get_verification()
            if precondition is KPValue.FALSE:
                test_case_result = TestResult.Result.SKIPPED
            elif failure is KPValue.TRUE:
                test_case_result = TestResult.Result.FAILED
            elif success is KPValue.TRUE:
                test_case_result = TestResult.Result.SUCCEEDED
            else:
                self._request_control_avs(vids.vids)
                freq = Num()
                freq.num = ai_frequency
                self.send_message_to_sim_node(b"steps", [self.serialized_sid, freq.SerializeToString()])
        result = TestResult()
        result.result = test_case_result
        self.send_message_to_sim_node(b"stop", [self.serialized_sid, result.SerializeToString()], 10)

    @static_vars(port=64256, lock=Lock())
    def _start_simulation(self, test_case: TestCase) -> Tuple[Scenario, ExtThread]:
        from threading import Thread
        from config import BEAMNG_INSTALL_FOLDER, BEAMNG_LEVEL_NAME

        home_path = BEAMNG_INSTALL_FOLDER
        user_path = self.get_user_path()

        Simulation._start_simulation.lock.acquire()
        while not Simulation._is_port_available(Simulation._start_simulation.port):
            Simulation._start_simulation.port += 100  # Make sure to not interfere with previously started simulations
        bng_instance = DBBeamNGpy('localhost', Simulation._start_simulation.port, home=home_path, user=user_path)
        authors = ", ".join(test_case.authors)
        bng_scenario = Scenario(BEAMNG_LEVEL_NAME, self.sid.sid, authors=authors)

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
        test_case.scenario.set_time_of_day_to(bng_instance)
        bng_instance.hide_hud()
        bng_instance.start_scenario()
        bng_instance.pause()
        Simulation._start_simulation.lock.release()

        runtime_thread = Thread(target=Simulation._run_runtime_verification, args=(self, test_case.aiFrequency))
        runtime_thread.daemon = True
        runtime_thread.start()

        while not runtime_thread.ident:  # Wait for the Thread to get an ID
            pass
        return bng_scenario, ExtThread(runtime_thread.ident)


@static_vars(counter=0)
def run_test_case(test_case: TestCase) -> Tuple[Simulation, Scenario, ExtThread]:
    """
    This method starts the actual simulation in a separate thread.
    Additionally it already calculates and attaches all information that is need by this node and the separate
    thread before calling _start_simulation(...).
    """
    import dill as pickle
    from shutil import rmtree
    from common import send_message, create_client
    from config import SIM_NODE_PORT, FIRST_SIM_PORT
    sid = SimulationID()
    response = send_message(create_client("localhost", SIM_NODE_PORT), b"generateSid", [], None)
    sid.ParseFromString(response)
    sim = Simulation(sid, pickle.dumps(test_case), FIRST_SIM_PORT + run_test_case.counter)
    run_test_case.counter += 1  # FIXME Add a lock?
    # Make sure there is no folder of previous tests having the same sid that got not propery removed
    rmtree(sim.get_user_path(), ignore_errors=True)
    bng_scenario, thread = sim._start_simulation(test_case)

    return sim, bng_scenario, thread
