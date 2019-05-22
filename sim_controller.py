from typing import List

from beamngpy import Scenario

from dbtypes.criteria import TestCase
from dbtypes.scheme import Participant


def enable_participant_movements(participants: List[Participant]) -> None:
    """
    Adds triggers to the scenario that set the next waypoints for the given participants. Must be called after adding
    the waypoints. Otherwise some IDs of waypoints may be None.
    :param participants: The participants to add movement changing triggers to
    """
    from util import add_to_prefab_file, eprint, get_lua_path
    from dbtypes.scheme import MovementMode
    lua_file = open(get_lua_path(), "w")
    lua_file.writelines([  # FIXME Is this needed somehow?
        "local M = {}\n",
        "\n",
        "local function onRaceStart()\n",
        "  log('I', 'Test','onRaceStart called ')\n",
        "end\n",
        "\n",
        "local function onBeamNGTrigger(data)\n",
        "  log('I', 'Test','onBeamNGTrigger called ')\n",
        "  dump(data)\n",
        "end\n",
        "\n",
        "M.onRaceStart = onRaceStart\n",
        "M.onBeamNGTrigger = onBeamNGTrigger\n",
        "return M"
    ])

    for participant in participants:
        for idx, waypoint in enumerate(participant.movement[:-1]):
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
                if waypoint.mode is MovementMode.MANUAL:
                    # FIXME If previous waypoint already had the mode MANUAL do not change the route
                    # FIXME Recognize speed (limits)
                    lua_lines.extend([
                        "    sh.setAiRoute('" + participant.id + "', " + remaining_waypoints + ")"
                    ])
                else:
                    eprint("Mode " + str(waypoint.mode) + " not supported, yet.")
                lua_lines.extend([
                    "  end",
                    "end",
                    "",
                    "return onWaypoint"
                ])
                return "\\r\\n".join(lua_lines)

            remaining_waypoints = "{'" + "', '".join(map(lambda w: w.id, participant.movement[idx + 1:])) + "'}"
            add_to_prefab_file([
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


def make_lanes_visible() -> None:
    """
    Workaround for making lanes visible.
    """
    from util import get_prefab_path
    prefab_file_path = get_prefab_path()
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


def start_moving_participants(participants: List[Participant], scenario: Scenario) -> None:
    """
    Makes cars move. Must be called after starting the scenario.
    :param participants: The participants whose movements have to be added.
    :param scenario: The scenario to add movements of participants to.
    """
    from beamngpy import Vehicle
    from util import eprint
    for participant in participants:
        vehicle: Vehicle = scenario.get_vehicle(participant.id)
        if vehicle is None:
            eprint("Vehicle to add movement to not found. You may wan to add vehicles first.")
        else:
            # FIXME The movement from first to second waypoint is not fluent
            # FIXME Recognize movement mode of first waypoint
            vehicle.ai_set_waypoint(participant.movement[0].id)


def run_test_case(test_case: TestCase):
    from app import app
    from dbtypes.beamng import DBBeamNGpy
    from dbtypes.criteria import KPValue
    from shutil import rmtree
    import os
    home_path = app.config["BEAMNG_INSTALL_FOLDER"]
    user_path = app.config["BEAMNG_USER_PATH"]

    # Make sure there is no inference with previous tests while keeping the cache
    rmtree(os.path.join(user_path, "levels"))

    # FIXME Determine port and host automatically. (Is it required to do so?)
    bng_instance = DBBeamNGpy('localhost', 64256, home=home_path, user=user_path)
    authors = ", ".join(test_case.authors)
    bng_scenario = Scenario(app.config["BEAMNG_LEVEL_NAME"], app.config["BEAMNG_SCENARIO_NAME"], authors=authors)
    test_case.scenario.add_all(bng_scenario)
    bng_scenario.make(bng_instance)

    make_lanes_visible()
    # FIXME As long as manually inserting text it can only be called after make
    test_case.scenario.add_waypoints_to_scenario(bng_scenario)
    enable_participant_movements(test_case.scenario.participants)

    bng_instance.open(launch=True)
    try:
        bng_instance.load_scenario(bng_scenario)
        bng_instance.start_scenario()
        start_moving_participants(test_case.scenario.participants, bng_scenario)

        precondition = test_case.precondition_fct(bng_scenario)
        failure = test_case.failure_fct(bng_scenario)
        success = test_case.success_fct(bng_scenario)
        test_case_result = "undetermined"
        while test_case_result == "undetermined":
            bng_instance.pause()
            for participant in test_case.scenario.participants:
                vehicle = bng_scenario.get_vehicle(participant.id)
                vehicle.update_vehicle()
            if precondition.eval() is KPValue.FALSE:
                test_case_result = "skipped"
            elif failure.eval() is KPValue.TRUE:
                test_case_result = "failed"
            elif success.eval() is KPValue.TRUE:
                test_case_result = "succeeded"
            else:
                # test_case_result = "undetermined"
                bng_instance.step(test_case.frequency)
        print("Test case result: " + test_case_result)
    finally:
        bng_instance.close()
