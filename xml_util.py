import os
from typing import Tuple, Union

from lxml import etree
from lxml.etree import ElementTree, Element

from common import eprint, is_dbe, is_dbc

XSD_FILE_PATH = os.path.join(os.path.dirname(__file__), "../schemes/drivebuild.xsd")
SCHEMA_ROOT = etree.parse(XSD_FILE_PATH)
SCHEMA = etree.XMLSchema(SCHEMA_ROOT)
PARSER = etree.XMLParser(schema=SCHEMA, recover=False)
NAMESPACES = {
    "db": "http://drivebuild.com"
}


def validate(path: str) -> Tuple[bool, ElementTree]:
    valid: bool = False
    parsed: ElementTree = None
    if is_dbe(path) or is_dbc(path):
        try:
            parsed = etree.parse(path, PARSER)
            valid = SCHEMA.validate(parsed)
        except etree.XMLSyntaxError as e:
            eprint(e)
    return valid, parsed


def xpath(xml_tree: Union[Element, ElementTree], expression: str) -> list:
    return xml_tree.xpath(expression, namespaces=NAMESPACES)
