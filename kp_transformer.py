from typing import Dict, Callable, Union, Tuple

from beamngpy import Scenario
from lxml.etree import _ElementTree, _Element

from common import string_to_shape
from dbtypes.criteria import VCPosition, SCPosition, VCArea, Evaluable, ValidationConstraint, \
    SCArea, SCLane, VCLane, SCSpeed, VCSpeed, SCDamage, VCDamage, VCTime, SCDistance, VCDistance, VCTTC, SCLight, \
    VCLight, SCWaypoint, VCWaypoint, Connective, And, Or, Not, CriteriaFunction
from dbtypes.scheme import CarLight

AnyStateCondition = Union[SCPosition, SCArea, SCLane, SCSpeed, SCDamage, SCDistance, SCLight, SCWaypoint]
sc_options: Dict[str, Callable[[_Element], Callable[[Scenario], AnyStateCondition]]] = {
    "scPosition": lambda node: lambda scenario: SCPosition(scenario, node.get("participant"), float(node.get("x")),
                                                           float(node.get("y")), float(node.get("tolerance"))),
    "scArea": lambda node: lambda scenario: SCArea(
        scenario, node.get("participant"), string_to_shape(node.get("points"))),
    "scLane": lambda node: lambda scenario: SCLane(scenario, node.get("participant"), node.get("lane")),
    "scSpeed": lambda node: lambda scenario: SCSpeed(scenario, node.get("participant"), float(node.get("limit"))),
    "scDamage": lambda node: lambda scenario: SCDamage(scenario, node.get("participant")),
    "scDistance": lambda node: lambda scenario: SCDistance(
        scenario, node.get("participant"), node.get("to"), float(node.get("max"))),
    "scLight": lambda node: lambda scenario: SCLight(scenario, node.get("participant"), CarLight[node.get("turnedOn")]),
    "scWaypoint": lambda node: lambda scenario: SCWaypoint(scenario, node.get("participant"), node.get("waypoint"))
}

vc_options: Dict[str, Callable[[_Element], Callable[[Scenario], ValidationConstraint]]] = {
    "vcPosition": lambda node: lambda scenario: VCPosition(
        scenario, generate_criterion(node[0])(scenario), sc_options["scPosition"](node)(scenario)),
    "vcArea": lambda node: lambda scenario: VCArea(
        scenario, generate_criterion(node[0])(scenario), sc_options["scArea"](node)(scenario)),
    "vcLane": lambda node: lambda scenario: VCLane(
        scenario, generate_criterion(node[0])(scenario), sc_options["scLane"](node)(scenario)),
    "vcSpeed": lambda node: lambda scenario: VCSpeed(
        scenario, generate_criterion(node[0])(scenario), sc_options["scSpeed"](node)(scenario)),
    "vcDamage": lambda node: lambda scenario: VCDamage(
        scenario, generate_criterion(node[0])(scenario), sc_options["scDamage"](node)(scenario)),
    "vcTime": lambda node: lambda scenario: VCTime(
        scenario, generate_criterion(node[0])(scenario), int(node.get("from")), int(node.get("to"))),
    "vcDistance": lambda node: lambda scenario: VCDistance(
        scenario, generate_criterion(node[0])(scenario), sc_options["scDistance"](node)(scenario)),
    "vcTTC": lambda node: lambda scenario: VCTTC(scenario, generate_criterion(node[0])(scenario)),
    "vcLight": lambda node: lambda scenario: VCLight(
        scenario, generate_criterion(node[0])(scenario), sc_options["scLight"](node)(scenario)),
    "vcWaypoint": lambda node: lambda scenario: VCWaypoint(
        scenario, generate_criterion(node[0])(scenario), sc_options["scWaypoint"](node)(scenario))
}

connective_options: Dict[str, Callable[[_Element], Callable[[Scenario], Connective]]] = {
    "and": lambda node: lambda scenario: And(
        [generate_criterion(child_node)(scenario) for child_node in node.iterchildren()]),
    "or": lambda node: lambda scenario: Or(
        [generate_criterion(child_node)(scenario) for child_node in node.iterchildren()]),
    "not": lambda node: lambda scenario: Not(generate_criterion(node[0])(scenario))
}


def generate_criterion(root: _Element) -> CriteriaFunction:
    from xml_util import get_tag_name
    tag = get_tag_name(root)
    print(tag)
    if tag in ["precondition", "success", "failure"]:
        evaluation = generate_criterion(root[0])
    elif tag in sc_options:
        evaluation = sc_options[tag]
    elif tag in vc_options:
        evaluation = vc_options[tag]
    elif tag in connective_options:
        evaluation = connective_options[tag]
    else:
        raise ValueError("Element " + tag + " can not be handled.")
    return evaluation(root)


def generate_criteria(crit_def: _ElementTree) -> Tuple[CriteriaFunction, CriteriaFunction, CriteriaFunction]:
    """
    Generates a tuple containing functions evaluating criteria.
    :param crit_def: The criteria root element.
    :return: A tuple representing functions for evaluating criteria. The first is for preconditions, the second for
    success criteria and the third for fail criteria.
    """
    from dbtypes.criteria import UnknownEvaluable
    from xml_util import xpath
    root: _Element = crit_def.getroot()
    preconditions_nodes = xpath(root, "db:precondition")
    precondition = generate_criterion(preconditions_nodes[0]) \
        if preconditions_nodes is None else (lambda _: UnknownEvaluable())
    success_nodes = xpath(root, "db:success")
    success = generate_criterion(success_nodes[0]) if success_nodes else (lambda _: UnknownEvaluable())
    failure_nodes = xpath(root, "db:failure")
    failure = generate_criterion(failure_nodes[0]) if failure_nodes is None else (lambda _: UnknownEvaluable())
    return precondition, success, failure
