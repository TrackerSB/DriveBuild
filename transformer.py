from typing import List

from db_types import ScenarioMapping, TestCase
from generator import generate_scenario
from kp_transformer import generate_criteria
from xml_util import xpath


def transform(mappings: List[ScenarioMapping]) -> List[TestCase]:
    test_cases = list()
    for mapping in mappings:
        for crit_def in mapping.crit_defs:
            participants = xpath(crit_def, "db:participants")
            builder = generate_scenario(mapping.environment, participants)
            criteria = generate_criteria(crit_def)
            test_cases.append(TestCase(builder, criteria))
    return test_cases
