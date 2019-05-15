import os
from typing import List


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


def get_prefab_path() -> str:
    from app import app
    return os.path.join(
        app.config["BEAMNG_USER_PATH"],
        "levels",
        app.config["BEAMNG_LEVEL_NAME"],
        "scenarios",
        app.config["BEAMNG_SCENARIO_NAME"] + ".prefab"
    )


def add_to_prefab_file(new_content: List[str]) -> None:
    """
    Workaround for adding content to a scenario prefab if there is no explicit method for it.
    :param new_content: The lines of content to add.
    """
    prefab_file_path = get_prefab_path()
    prefab_file = open(prefab_file_path, "r")
    original_content = prefab_file.readlines()
    prefab_file.close()
    for line in new_content:
        original_content.insert(-2, line + "\n")
    prefab_file = open(prefab_file_path, "w")
    prefab_file.writelines(original_content)
    prefab_file.close()
