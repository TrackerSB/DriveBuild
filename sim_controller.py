from typing import List

from beamngpy import Scenario

from db_types import TestCase, Participant


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
            path = [{
                'pos': (wp.position[0], wp.position[1], 0),  # FIXME Recognize z-offset of car model
                'speed': wp.target_speed
            } for wp in participant.movement]
            vehicle.ai_set_line(path)


def run_test_case(test_case: TestCase):
    from app import app
    from beamngpy import BeamNGpy
    # user_path = mkdtemp(prefix="drivebuild_beamng_")  # FIXME user_path not working
    # FIXME Determine port and host automatically
    bng_instance = BeamNGpy('localhost', 64256, home=app.config["BEAMNG_INSTALL_FOLDER"])
    authors = ", ".join(test_case.authors)
    bng_scenario = Scenario("smallgrid", "Test", authors=authors)  # FIXME Generate name for scenario
    test_case.scenario.add_all(bng_scenario)
    bng_scenario.make(bng_instance)
    bng_instance.open(launch=True)
    try:
        bng_instance.load_scenario(bng_scenario)
        bng_instance.start_scenario()
        add_movements_to_scenario(test_case.scenario.participants, bng_scenario)
        input("Press enter to end...")
    finally:
        bng_instance.close()
