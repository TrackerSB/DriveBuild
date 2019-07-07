from typing import Tuple, List, Dict

from lxml.etree import _ElementTree

from dbtypes import SimulationData
from dbtypes.scheme import ScenarioMapping
from sim_controller import Simulation


def extract_test_cases(zip_content: bytes) -> str:
    import zipfile
    from tempfile import mkdtemp, mkstemp
    _, zip_file_name = mkstemp(suffix=".zip")
    zip_file = open(zip_file_name, "w+b")
    zip_file.write(zip_content)
    zip_ref = zipfile.ZipFile(zip_file, 'r')
    temp_dir = mkdtemp(prefix="drivebuild_")
    zip_ref.extractall(temp_dir)
    zip_ref.close()
    return temp_dir


def associate_criteria(mapping_stubs: List[ScenarioMapping], criteria_defs: List[_ElementTree]) \
        -> List[ScenarioMapping]:
    from common import eprint
    from util.xml import xpath
    for criteria_def in criteria_defs:
        for element in xpath(criteria_def, "db:environment"):
            needed_environment = element.text
            found_env = False
            for stub in mapping_stubs:
                if needed_environment == stub.filename:
                    stub.crit_defs.append(criteria_def)
                    found_env = True
                    break
            if not found_env:
                eprint("A criteria definition needs " + needed_environment
                       + " but it is either not valid or not available")
    return [mapping for mapping in mapping_stubs if mapping.crit_defs]


def get_valid(folder: str) -> Tuple[List[ScenarioMapping], List[_ElementTree]]:
    import os
    from common import eprint
    from util import is_dbe, is_dbc
    from util.xml import validate
    scenario_mapping_stubs = list()
    valid_crit_defs = list()
    for filename in os.listdir(folder):
        path = os.path.join(folder, filename)
        valid, root = validate(path)
        if valid:
            if is_dbe(path):
                scenario_mapping_stubs.append(ScenarioMapping(root, filename))
            elif is_dbc(path):
                valid_crit_defs.append(root)
            else:
                eprint(filename + " is valid but can not be classified as DBE or DBC.")
    return scenario_mapping_stubs, valid_crit_defs


def run_tests(zip_file_content: bytes) -> Dict[Simulation, SimulationData]:
    from common import eprint
    from sim_controller import run_test_case
    from transformer import transform
    from datetime import datetime
    folder = extract_test_cases(zip_file_content)
    mapping_stubs, valid_crit_defs = get_valid(folder)

    simulations = {}
    mapping = associate_criteria(mapping_stubs, valid_crit_defs)
    if mapping:
        test_cases = transform(mapping)
        for test_case, crit_def, env_def in test_cases:
            sim, bng_scenario, thread = run_test_case(test_case)
            data = SimulationData(bng_scenario, thread, crit_def, env_def)
            data.start_time = datetime.now()
            simulations[sim] = data
    else:
        eprint("Some criteria definitions have no valid environment.")
    return simulations
