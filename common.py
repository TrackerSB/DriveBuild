import sys


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def is_dbe(filename_path: str) -> bool:
    return filename_path.endswith(".dbe.xml")


def is_dbc(filename_path: str) -> bool:
    return filename_path.endswith(".dbc.xml")
