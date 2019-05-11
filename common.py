def eprint(*args, **kwargs):
    from sys import stderr
    print(*args, file=stderr, **kwargs)


def is_dbe(filename_path: str) -> bool:
    return filename_path.endswith(".dbe.xml")


def is_dbc(filename_path: str) -> bool:
    return filename_path.endswith(".dbc.xml")
