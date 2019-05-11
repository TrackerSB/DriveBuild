def eprint(*args, **kwargs):
    from sys import stderr
    print(*args, file=stderr, **kwargs)


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
