from typing import Tuple, List, Dict, Union

from lxml.etree import _ElementTree

from dbtypes import SimulationData
from dbtypes.scheme import ScenarioMapping
from sim_controller import Simulation


def extract_test_cases(zip_content: bytes) -> str:
    import zipfile
    from tempfile import mkdtemp, NamedTemporaryFile
    from os import remove
    with NamedTemporaryFile(mode="w+b", suffix=".zip", delete=False) as zip_file:
        zip_file.write(zip_content)
    with zipfile.ZipFile(zip_file.name, "r") as zip_ref:
        temp_dir = mkdtemp(prefix="drivebuild_")
        zip_ref.extractall(temp_dir)
    remove(zip_file.name)
    return temp_dir


def associate_criteria(mapping_stubs: List[ScenarioMapping], criteria_defs: List[_ElementTree]) \
        -> List[ScenarioMapping]:
    from drivebuildclient.common import eprint
    from util.xml import xpath
    for criteria_def in criteria_defs:
        for element in xpath(criteria_def, "db:environment"):
            needed_environment = element.text.strip()
            found_env = False
            for stub in mapping_stubs:
                if needed_environment == stub.filename:
                    stub.crit_defs.append(criteria_def)
                    found_env = True
                    break
            if not found_env:
                if needed_environment:
                    eprint("A criteria definition needs " + needed_environment
                           + " but it is either not valid or not available")
                else:
                    eprint("A criteria definition is missing a declaration of an associated environment.")
    return [mapping for mapping in mapping_stubs if mapping.crit_defs]


def get_valid(folder: str) -> Tuple[List[ScenarioMapping], List[_ElementTree]]:
    import os
    from drivebuildclient.common import eprint
    from util import is_dbe, is_dbc
    from util.xml import validate
    scenario_mapping_stubs = list()
    valid_crit_defs = list()
    for filename in os.listdir(folder):
        path = os.path.join(folder, filename)
        valid, root = validate(path)
        if valid and root:
            if is_dbe(root):
                scenario_mapping_stubs.append(ScenarioMapping(root, filename))
            elif is_dbc(root):
                valid_crit_defs.append(root)
            else:
                eprint(filename + " is valid but can not be classified as DBE or DBC.")
    return scenario_mapping_stubs, valid_crit_defs


def run_tests(zip_file_content: bytes) -> Union[Dict[Simulation, SimulationData], str]:
    from sim_controller import run_test_case
    from transformer import transform
    from datetime import datetime
    folder = extract_test_cases(zip_file_content)
    mapping_stubs, valid_crit_defs = get_valid(folder)

    mapping = associate_criteria(mapping_stubs, valid_crit_defs)
    if mapping:
        simulations = {}
        test_cases = transform(mapping)
        for test_case, crit_def, env_def in test_cases:
            sim, bng_scenario, thread = run_test_case(test_case)
            data = SimulationData(bng_scenario, thread, crit_def, env_def)
            data.start_time = datetime.now()
            simulations[sim] = data
        return simulations
    else:
        return "No valid tests submitted."
