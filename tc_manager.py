import os
import zipfile
from tempfile import mkdtemp
from typing import Tuple, List

from lxml.etree import _ElementTree
from werkzeug.datastructures import FileStorage

from common import eprint, is_dbe, is_dbc
from transformer import transform
from xml_util import validate, xpath


def extract_test_cases(zip_file: FileStorage) -> str:
    zip_ref = zipfile.ZipFile(zip_file, 'r')
    temp_dir = mkdtemp(prefix="drivebuild_")
    zip_ref.extractall(temp_dir)
    zip_ref.close()
    return temp_dir


def is_complete(environment_filenames: List[str], criteria_defs: List[_ElementTree]) -> bool:
    complete = True
    for criteria_def in criteria_defs:
        for element in xpath(criteria_def, "db:environment"):
            needed_environment = element.text
            if needed_environment not in environment_filenames:
                eprint("A criteria definition needs " + needed_environment
                       + " but it is either not valid or not available")
                complete = False
    return complete


def get_valid(folder: str) -> Tuple[List[_ElementTree], List[_ElementTree]]:
    valid_envs = list()
    valid_crit_defs = list()
    for filename in os.listdir(folder):
        path = os.path.join(folder, filename)
        valid, root = validate(path)
        if valid:
            if is_dbe(path):
                valid_envs.append(root)
            elif is_dbc(path):
                valid_crit_defs.append(root)
            else:
                eprint(filename + " is valid but can not be classified as DBE or DBC.")
    return valid_envs, valid_crit_defs


def execute_tests(zip_file: FileStorage) -> None:
    folder = extract_test_cases(zip_file)
    valid_envs, valid_crit_defs = get_valid(folder)

    if is_complete(valid_envs, valid_crit_defs):
        envs, crit_defs = transform(valid_envs, valid_crit_defs)
    else:
        eprint("Some criteria definitions have no valid environment.")
