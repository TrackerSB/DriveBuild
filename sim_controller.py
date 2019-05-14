from typing import List

from beamngpy import Scenario

from db_types import TestCase, Participant


def enable_participant_movements(participants: List[Participant]) -> None:
    from app import app
    from common import add_to_prefab_file
    from db_types import WayPoint
    import os
    lua_file_path = os.path.join(
        app.config["BEAMNG_USER_PATH"],
        "levels",
        app.config["BEAMNG_LEVEL_NAME"],
        "scenarios",
        app.config["BEAMNG_SCENARIO_NAME"] + ".lua"
    )
    lua_file = open(lua_file_path, "w")
    lua_file.writelines([
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

    def to_inline_lua(lines: List[str]) -> str:
        return "\\r\\n".join(lines)

    for participant in participants:
        waypoints = [WayPoint(participant.initial_state.position, 0)]
        waypoints.extend(participant.movement)
        for waypoint in waypoints:
            x_pos = waypoint.position[0]
            y_pos = waypoint.position[1]
            # NOTE Add further tolerance for oversize of bounding box compared to the actual car
            tolerance = waypoint.tolerance + 0.5
            add_to_prefab_file([
                "new BeamNGTrigger() {",
                "    TriggerType = \"Sphere\";",
                "    TriggerMode = \"Overlaps\";",
                "    TriggerTestType = \"Race Corners\";",
                "    luaFunction = \""
                + to_inline_lua([
                    "local res = require('vehicle/extensions/researchVE')",
                    "local function onWaypoint(data)",
                    "  dump(data)",
                    "  local vehicle = be:getObjectByID(data['subjectID'])",
                    "  dump(vehicle)",
                    "  print(vehicle:getField('position', '0'))",
                    "  res.handleSetAiLine({",
                    "    cling = true,",
                    "    line = { {",
                    "      pos = { 10, 20, 0},",
                    "      speed = 60",
                    "    } },",
                    "    type = \\\"SetAiLine\\\"",
                    "  })",
                    "end",
                    "",
                    "return onWaypoint"
                ])
                + "\";",
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
    from common import get_prefab_path
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
    from common import eprint
    for participant in participants:
        vehicle: Vehicle = scenario.get_vehicle(participant.id)
        if vehicle is None:
            eprint("Vehicle to add movement to not found. You may wan to add vehicles first.")
        else:
            # FIXME Recognize AIModes
            # FIXME Recognize speed limits
            # FIXME Recognize tolerances
            for waypoint in participant.movement:
                # vehicle.ai_set_waypoint(waypoint.id)  # FIXME Only approaches to the border of the waypoint
                vehicle.ai_set_line([{
                    'pos': (waypoint.position[0], waypoint.position[1], 0),  # FIXME Recognize z-offset of car model
                    'speed': waypoint.target_speed
                }])
                break  # FIXME Wait for reaching the waypoint and only then change it


def run_test_case(test_case: TestCase):
    from app import app
    from beamngpy import BeamNGpy
    from shutil import rmtree
    import os
    home_path = app.config["BEAMNG_INSTALL_FOLDER"]
    user_path = app.config["BEAMNG_USER_PATH"]

    # Make sure there is no inference with previous tests while keeping the cache
    rmtree(os.path.join(user_path, "levels"))

    # FIXME Determine port and host automatically. (Is it required to do so?)
    bng_instance = BeamNGpy('localhost', 64256, home=home_path, user=user_path)
    authors = ", ".join(test_case.authors)
    bng_scenario = Scenario(app.config["BEAMNG_LEVEL_NAME"], app.config["BEAMNG_SCENARIO_NAME"], authors=authors)
    test_case.scenario.add_all(bng_scenario)
    bng_scenario.make(bng_instance)

    enable_participant_movements(test_case.scenario.participants)
    make_lanes_visible()
    # FIXME As long as manually inserting text it can only be called after make
    # test_case.scenario.add_waypoints_to_scenario(bng_scenario)

    bng_instance.open(launch=True)
    try:
        bng_instance.load_scenario(bng_scenario)
        bng_instance.start_scenario()
        bng_scenario.get_vehicle("ego").ai_set_line([{
            'pos': (15, 25, 0),
            'speed': 65
        }])
        # start_moving_participants(test_case.scenario.participants, bng_scenario)
        input("Press enter to end...")
    finally:
        bng_instance.close()
