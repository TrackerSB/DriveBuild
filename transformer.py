from typing import List, Tuple

from lxml.etree import _ElementTree

from dbtypes.criteria import TestCase
from dbtypes.scheme import ScenarioMapping


def get_author(root: _ElementTree) -> str:
    from util.xml import xpath
    return xpath(root, "db:author")[0].text


def transform(mappings: List[ScenarioMapping]) -> List[Tuple[TestCase, _ElementTree, _ElementTree]]:
    """
    Return tuples containing the generated test case, its criteria definition and its environment
    """
    from generator import generate_scenario
    from kp_transformer import generate_criteria
    from util.xml import xpath
    test_cases = list()
    for mapping in mappings:
        environment = mapping.environment
        environment_author = get_author(environment)
        for crit_def, crit_content in mapping.crit_defs:
            ai_frequency = int(xpath(crit_def, "db:aiFrequency")[0].text)
            steps_per_second = int(xpath(crit_def, "db:stepsPerSecond")[0].text)
            participants_node = xpath(crit_def, "db:participants")[0]
            builder = generate_scenario(environment, participants_node)
            precondition, success, failure = generate_criteria(crit_def)
            crit_def_author = get_author(crit_def)
            authors = [environment_author]
            if crit_def_author not in authors:
                authors.append(crit_def_author)
            test_cases.append(
                (TestCase(builder, precondition, success, failure, steps_per_second, ai_frequency, authors),
                 crit_def, environment)
            )
    return test_cases
