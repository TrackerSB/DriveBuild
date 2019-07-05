import os
from typing import Tuple, Union, List, Optional

from lxml import etree
from lxml.etree import _ElementTree, _Element

XSD_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "schemes", "drivebuild.xsd")
SCHEMA_ROOT = etree.parse(XSD_FILE_PATH)
SCHEMA = etree.XMLSchema(SCHEMA_ROOT)
PARSER = etree.XMLParser(schema=SCHEMA, recover=False)
NAMESPACES = {
    "db": "http://drivebuild.com"
}


def validate(path: str) -> Tuple[bool, Optional[_ElementTree]]:
    from common import eprint
    from util import is_dbe, is_dbc
    valid: bool = False
    parsed: Optional[_ElementTree] = None
    if is_dbe(path) or is_dbc(path):
        try:
            parsed = etree.parse(path, PARSER)
            valid = SCHEMA.validate(parsed)
        except etree.XMLSyntaxError as e:
            eprint(e)
    return valid, parsed


def xpath(xml_tree: Union[_Element, _ElementTree], expression: str) -> Union[List[_Element], _ElementTree]:
    return xml_tree.xpath(expression, namespaces=NAMESPACES)


def has_tag(node: _Element, namespace: Optional[str], tag_name: str) -> bool:
    if namespace in NAMESPACES:
        if namespace is None:
            prefix = ""
        else:
            prefix = "{" + NAMESPACES[namespace] + "}"
        return node.tag == (prefix + tag_name)
    else:
        raise ValueError("There is no namespace " + namespace)


def get_tag_name(node: _Element) -> str:
    return node.tag.split("}")[1] if "}" in node.tag else node.tag
