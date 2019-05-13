from typing import List

from beamngpy import Scenario

from db_types import TestCase, Participant


def add_trigger_for_changing_waypoint() -> None:
    from app import app
    from common import add_to_prefab_file
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
        "map = require(\"map\")\n",
        "\n",
        "local function onWaypoint(args)\n",
        "  log('I', 'Test','onWaypoint called ')\n",
        "end\n",
        "\n",
        "local function onBeamNGWaypoint(args)\n",
        "  log('I', 'Test','onBeamNGWaypoint called ')\n",
        "end\n",
        "\n",
        "local function onRaceWaypointReached(args)\n",
        "  log('I', 'Test','onRaceWaypointReached called ')\n",
        "end\n",
        "\n",
        "local function onRaceStart()\n",
        "  log('I', 'Test','onRaceStart called ')\n",
        "end\n",
        "\n",
        "local function onBeamNGTrigger()\n",
        "  log('I', 'Test','onBeamNGTrigger called ')\n",
        "end\n",
        "\n",
        "M.onWaypoint = onWaypoint\n",
        "M.onBeamNGWaypoint = onBeamNGWaypoint\n",
        "M.onRaceWaypointReached = onRaceWaypointReached\n",
        "M.onRaceStart = onRaceStart\n",
        "M.onBeamNGTrigger = onBeamNGTrigger\n",
        "return M"
    ])

    add_to_prefab_file([
        "new BeamNGTrigger(pierTrigger) {",
        "    TriggerType = \"Sphere\";",
        "    TriggerMode = \"Overlaps\";",
        "    TriggerTestType = \"Bounding Box\";",
        "    luaFunction = \"onBeamNGTrigger\";",
        "    tickPeriod = \"100\";",
        "    debug = \"0\";",
        "    ticking = \"0\";",
        "    triggerColor = \"255 192 0 45\";",
        # "    cameraOnEnter = \"pierCamera\";",
        "    defaultOnLeave = \"1\";",
        "    position = \"10 0 0\";",
        "    scale = \"20 20 20\";",
        "    rotationMatrix = \"0 0 0 0 0 0 0 0 0\";",
        "    mode = \"Ignore\";",
        "    canSave = \"1\";",
        "    canSaveDynamicFields = \"1\";",
        "};"
    ])


def make_lanes_visible() -> None:
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


def add_movements_to_scenario(participants: List[Participant], scenario: Scenario) -> None:
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
            # path = [{
            #     'pos': (wp.position[0], wp.position[1], 0),  # FIXME Recognize z-offset of car model
            #     'speed': wp.target_speed
            # } for wp in participant.movement]
            # vehicle.ai_set_line(path)
            for waypoint in participant.movement:
                vehicle.ai_set_waypoint(waypoint.id)
                break  # FIXME Wait for reaching the waypoint and only then change it


def run_test_case(test_case: TestCase):
    from app import app
    from beamngpy import BeamNGpy
    home_path = app.config["BEAMNG_INSTALL_FOLDER"]
    user_path = app.config["BEAMNG_USER_PATH"]
    # FIXME Determine port and host automatically. (Is it required to do so?)
    bng_instance = BeamNGpy('localhost', 64256, home=home_path, user=user_path)
    authors = ", ".join(test_case.authors)
    bng_scenario = Scenario(app.config["BEAMNG_LEVEL_NAME"], app.config["BEAMNG_SCENARIO_NAME"], authors=authors)
    test_case.scenario.add_all(bng_scenario)
    bng_scenario.make(bng_instance)

    add_trigger_for_changing_waypoint()
    make_lanes_visible()
    # FIXME As long as manually inserting text it can only be called after make
    test_case.scenario.add_waypoints_to_scenario(bng_scenario)

    bng_instance.open(launch=True)
    try:
        bng_instance.load_scenario(bng_scenario)
        bng_instance.start_scenario()
        add_movements_to_scenario(test_case.scenario.participants, bng_scenario)
        input("Press enter to end...")
    finally:
        bng_instance.close()
