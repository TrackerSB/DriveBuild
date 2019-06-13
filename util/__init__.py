import re
from typing import List, Optional

from dbtypes.scheme import Position


def eprint(*args, **kwargs):
    from sys import stderr
    print(*args, file=stderr, **kwargs)  # TODO Is there some warn(...) equivalent function?


def is_dbe(filename_path: str) -> bool:
    return filename_path.endswith(".dbe.xml")


def is_dbc(filename_path: str) -> bool:
    return filename_path.endswith(".dbc.xml")


def static_vars(**kwargs):
    """
    Decorator hack for introducing local static variables.
    :param kwargs: The declarations of the static variables like "foo=42".
    :return: The decorated function.
    """

    def decorate(func):
        """
        Decorates the given function with local static variables based on kwargs.
        :param func: The function to decorate.
        :return: The decorated function.
        """
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func

    return decorate


@static_vars(pattern=re.compile(r"\(-?\d+,-?\d+\)(;\(-?\d+,-?\d+\))*"))
def is_valid_shape_string(pos_str: str) -> bool:
    """
    Checks whether the given string is of the form "(x_1,y_1);(x_2,y_2);...;(x_n,y_n)".
    :return: True only if the given string is of the right form.
    """
    return is_valid_shape_string.pattern.match(pos_str)


def string_to_shape(shape_string: str) -> Optional[List[Position]]:
    """
    Converts strings like "(x_1,y_1);(x_2,y_2);...;(x_n,y_n)" to a list of positions.
    :return: The list of positions represented by the given string
    """
    if is_valid_shape_string(shape_string):
        positions = list()
        position_strings = shape_string.split(";")
        for pos_str in position_strings:
            vals = pos_str.split(",")
            x_val = vals[0][1:]
            y_val = vals[1][:-1]
            positions.append((int(x_val), int(y_val)))
        return positions
    else:
        return None
