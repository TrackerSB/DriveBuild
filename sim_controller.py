from db_types import TestCase


def run_test_case(test_case: TestCase):
    from app import app
    from beamngpy import Scenario, BeamNGpy
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
        input("Press enter to end...")
        roads = bng_instance.get_roads()
    finally:
        bng_instance.close()
