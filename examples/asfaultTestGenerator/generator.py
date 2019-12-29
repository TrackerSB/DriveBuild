from os import remove
from os.path import basename
from tempfile import NamedTemporaryFile
from typing import Dict, List

from drivebuildclient.AIExchangeService import AIExchangeService
from jinja2 import Environment, FileSystemLoader

from drivebuildclient.aiExchangeMessages_pb2 import VehicleID, SimStateResponse
from asfault.tests import RoadTest
from drivebuildclient.common import eprint

ENV_SIZE: float = 100
TEMPLATE_PATH = "templates"
TEMPLATE_ENV = Environment(loader=FileSystemLoader(TEMPLATE_PATH))
DBE_TEMPLATE_NAME = "environment.dbe.xml"
DBC_TEMPLATE_NAME = "criteria.dbc.xml"


def _configure_asfault() -> None:
    from asfault.config import init_configuration, load_configuration
    from tempfile import TemporaryDirectory
    temp_dir = TemporaryDirectory(prefix="testGenerator")
    init_configuration(temp_dir.name)
    load_configuration(temp_dir.name)


def _generate_test_id() -> str:
    return "test_id"


def _generate_asfault_test() -> RoadTest:
    from asfault.generator import RoadGenerator
    from asfault.tests import get_start_goal_coords
    from shapely.geometry import box
    from numpy.random.mtrand import randint
    test_id = _generate_test_id()
    while True:
        generator = RoadGenerator(box(-ENV_SIZE, -ENV_SIZE, ENV_SIZE, ENV_SIZE), randint(10000))
        test_stub = RoadTest(test_id, generator.network, None, None)
        while generator.grow() != generator.done:
            pass
        if test_stub.network.complete_is_consistent():
            candidates = generator.network.get_start_goal_candidates()
            # FIXME Choose candidate based on some ranking?
            if candidates:
                start, goal = candidates.pop()
                paths = generator.network.all_paths(start, goal)
                # FIXME Choose candidate based on some ranking?
                for path in paths:
                    start_coords, goal_coords = get_start_goal_coords(generator.network, start, goal)
                    test = RoadTest(test_id, generator.network, start_coords, goal_coords)
                    test.set_path(path)
                    return test


LaneNode = Dict[str, float]
Lane = List[LaneNode]


def _get_lanes(test: RoadTest) -> List[Lane]:
    from asfault.beamer import prepare_streets
    streets = prepare_streets(test.network)
    lanes_nodes = []
    for street in streets:
        lane_nodes = street["nodes"]
        for node in lane_nodes:
            node["width"] = float("{0:.2f}".format(round(node["width"], 2)))
    return list(map(lambda street: street["nodes"], streets))


def _generate_dbe(lanes: List[Lane]) -> str:
    return TEMPLATE_ENV.get_template(DBE_TEMPLATE_NAME) \
        .render(lanes=lanes)


def _generate_dbc(lane_to_follow: Lane, dbe_file_name: str) -> str:
    from numpy.ma import arctan2
    from numpy import rad2deg, pi, sin, cos, array
    goal = lane_to_follow[-1]
    current = lane_to_follow[0]
    current_pos = array([current["x"], current["y"]])
    next = lane_to_follow[1]
    next_pos = array([next["x"], next["y"]])
    delta = next_pos - current_pos
    initial_orientation_rad = arctan2(delta[1], delta[0])
    initial_orientation_deg = float("{0:.2f}".format(rad2deg(initial_orientation_rad)))

    r2 = 0.25 * current["width"]
    theta2 = initial_orientation_rad - 0.5 * pi
    offset = array([2.5 * cos(initial_orientation_rad), 2.5 * sin(initial_orientation_rad)])
    temp = current_pos + offset
    initial_position = temp + array([r2 * cos(theta2), r2 * sin(theta2)])
    initial_state = {"x": initial_position[0], "y": initial_position[1]}

    return TEMPLATE_ENV.get_template(DBC_TEMPLATE_NAME) \
        .render(initial_state=initial_state,
                initial_orientation=initial_orientation_deg,
                lane=lane_to_follow,
                dbe_file_name=dbe_file_name,
                goal=goal)


def _main() -> None:
    from pathlib import Path
    _configure_asfault()
    test = _generate_asfault_test()
    lanes = _get_lanes(test)

    dbe_content = _generate_dbe(lanes)
    temp_dbe_file = NamedTemporaryFile(mode="w", delete=False, suffix=".dbe.xml")
    temp_dbe_file.write(dbe_content)
    temp_dbe_file.close()

    # FIXME Choose lane based on some ranking?
    dbc_content = _generate_dbc(lanes[0], basename(temp_dbe_file.name))
    temp_dbc_file = NamedTemporaryFile(mode="w", delete=False, suffix=".dbc.xml")
    temp_dbc_file.write(dbc_content)
    temp_dbc_file.close()

    service = AIExchangeService("defender.fim.uni-passau.de", 8383)
    submission_result = service.run_tests("test", "test", Path(temp_dbe_file.name), Path(temp_dbc_file.name))
    if submission_result and submission_result.submissions:
        for test_name, sid in submission_result.submissions.items():
            vid = VehicleID()
            vid.vid = "ego"
            while True:
                sim_state = service.wait_for_simulator_request(sid, vid)
                if sim_state != SimStateResponse.SimState.RUNNING:
                    break
            print("Result of \"" + test_name + "\": " + service.get_result(sid))
            break  # NOTE Assume only one test was uploaded
    else:
        eprint("DriveBuild denied running the given test.")

    remove(temp_dbe_file.name)
    remove(temp_dbc_file.name)


if __name__ == "__main__":
    _main()
