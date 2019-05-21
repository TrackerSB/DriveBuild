from typing import List

from lxml.etree import _ElementTree

from dbtypes.criteria import TestCase
from dbtypes.scheme import ScenarioMapping


def get_author(root: _ElementTree) -> str:
    from xml_util import xpath
    return xpath(root, "db:author")[0].text


def transform(mappings: List[ScenarioMapping]) -> List[TestCase]:
    from generator import generate_scenario
    from kp_transformer import generate_criteria
    from xml_util import xpath
    test_cases = list()
    for mapping in mappings:
        environment = mapping.environment
        environment_author = get_author(environment)
        for crit_def in mapping.crit_defs:
            frequency = int(xpath(crit_def, "db:frequency")[0].text)
            participants_node = xpath(crit_def, "db:participants")[0]
            builder = generate_scenario(environment, participants_node)
            precondition, success, failure = generate_criteria(crit_def)
            crit_def_author = get_author(crit_def)
            authors = [environment_author]
            if crit_def_author not in authors:
                authors.append(crit_def_author)
            test_cases.append(TestCase(builder, precondition, success, failure, frequency, authors))
    return test_cases
