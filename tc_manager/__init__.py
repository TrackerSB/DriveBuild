import os
import zipfile
from tempfile import mkdtemp
from typing import Tuple

from lxml import etree
from werkzeug.datastructures import FileStorage

from common import eprint

XSD_FILE_PATH = os.path.join(os.path.dirname(__file__), "../schemes/drivebuild.xsd")
SCHEMA_ROOT = etree.parse(XSD_FILE_PATH)
SCHEMA = etree.XMLSchema(SCHEMA_ROOT)
PARSER = etree.XMLParser(schema=SCHEMA, recover=True)
NAMESPACES = {
    "db": "http://drivebuild.com"
}


def is_dbe(filename_path: str):
    return filename_path.endswith(".dbe.xml")


def is_dbc(filename_path: str):
    return filename_path.endswith(".dbc.xml")


def extract_test_cases(zip_file: FileStorage) -> str:
    zip_ref = zipfile.ZipFile(zip_file, 'r')
    temp_dir = mkdtemp(prefix="drivebuild_")
    zip_ref.extractall(temp_dir)
    zip_ref.close()
    return temp_dir


def check_xml(path: str) -> Tuple[bool, etree.ElementTree]:
    valid = False
    root = None
    if is_dbe(path) or is_dbc(path):
        try:
            root = etree.parse(path, PARSER)
            valid = True
        except etree.XMLSyntaxError as e:
            eprint(e)
    return valid, root


def is_complete(environment_filenames, criteria_defs) -> bool:
    complete = True
    for criteria_def in criteria_defs:
        for element in criteria_def.xpath("db:environment", namespaces=NAMESPACES):
            needed_environment = element.text
            if needed_environment not in environment_filenames:
                eprint("A criteria definition needs " + needed_environment
                       + " but it is either not valid or not available")
                complete = False
    return complete


def execute_tests(zip_file: FileStorage):
    folder = extract_test_cases(zip_file)
    environment_defs = list()
    environment_filenames = list()
    criteria_defs = list()
    for filename in os.listdir(folder):
        path = os.path.join(folder, filename)
        valid, root = check_xml(path)
        if valid:
            if is_dbe(path):
                environment_defs.append(root)
                environment_filenames.append(filename)
            elif is_dbc(path):
                criteria_defs.append(root)
            else:
                eprint(path + " is valid but neither a DBE nor a DBC.")

    if is_complete(environment_filenames, criteria_defs):
        eprint("The actual execution is not implemented yet.")
    else:
        eprint("Some criteria definitions have no valid environment.")
