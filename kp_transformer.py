from abc import ABC, abstractmethod

from lxml.etree import _ElementTree

from db_types import Criteria


def generate_criteria(crit_def: _ElementTree) -> Criteria:
    pass
