import os
from typing import Tuple, Union, List, Optional

from lxml import etree
from lxml.etree import _ElementTree, _Element

XSD_FILE_PATH = os.path.join(os.path.dirname(__file__), "schemes/drivebuild.xsd")
SCHEMA_ROOT = etree.parse(XSD_FILE_PATH)
SCHEMA = etree.XMLSchema(SCHEMA_ROOT)
PARSER = etree.XMLParser(schema=SCHEMA, recover=False)
NAMESPACES = {
    "db": "http://drivebuild.com"
}


def validate(path: str) -> Tuple[bool, Optional[_ElementTree]]:
    from common import eprint, is_dbe, is_dbc
    valid: bool = False
    parsed: Optional[_ElementTree] = None
    if is_dbe(path) or is_dbc(path):
        try:
            parsed = etree.parse(path, PARSER)
            valid = SCHEMA.validate(parsed)
        except etree.XMLSyntaxError as e:
            eprint(e)
    return valid, parsed


def xpath(xml_tree: Union[_Element, _ElementTree], expression: str) -> List[_Element]:
    return xml_tree.xpath(expression, namespaces=NAMESPACES)
