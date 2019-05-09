from typing import Tuple, List

from lxml.etree import ElementTree

from generator import generate_scenario, ScenarioBuilder
from kp_transformer import generate_criteria, Criteria


def transform(envs: List[ElementTree], crit_defs: List[ElementTree]) -> Tuple[List[ScenarioBuilder], List[Criteria]]:
    generated_envs = [generate_scenario(env) for env in envs]
    generated_criteria = [generate_criteria(crit_def) for crit_def in crit_defs]
    return generated_envs, generated_criteria
    # TODO Add movements to the participants
    # TODO Determine which sensors are needed and add them
