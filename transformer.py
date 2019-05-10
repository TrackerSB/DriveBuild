from typing import List

from db_types import ScenarioMapping, TestCase
from generator import generate_scenario
from kp_transformer import generate_criteria


def transform(mappings: List[ScenarioMapping]) -> List[TestCase]:
    test_cases = list()
    for mapping in mappings:
        lanes = list()
    return test_cases
