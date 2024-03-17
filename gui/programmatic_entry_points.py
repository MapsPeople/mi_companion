import typing
from typing import Dict


def list_submodules(a_module: object) -> list[str]:
    """
    Returns a list of all submodules of a module

    :param a_module: The module to list submodules from.
    :return: A list of the submodules of the given module
    """

    # We first respect __all__ attribute if it already defined.

    submodules = getattr(a_module, "__all__", None)
    if submodules:
        return submodules

    # Then, we respect module object itself to get imported submodules.
    # Warning: Initially, the module object will respect the `__init__.py`
    # file, if it does not exist, the object can partially load submodules
    # by code, so can lead `inspect` to return incomplete submodules list.

    import inspect

    submodules = [o[0] for o in inspect.getmembers(a_module) if inspect.ismodule(o[1])]
    if submodules:
        return submodules

    # Finally, we can just scan for submodules via pkgutil.
    import pkgutil

    # pkgutill will invoke `importlib.machinery.all_suffixes()`
    # to determine whether a file is a module, so if you get any
    # submodules that are unexpected to get, you need to check
    # this function to do the confirmation.
    # If you want to retrieve a directory as a submodule, you will
    # need to clarify this by putting a `__init__.py` file in the
    # folder, even for Python3.
    return [x.name for x in pkgutil.iter_modules(a_module.__path__)]


def get_entry_points(module_: object) -> Dict[str, callable]:
    entry_points_ = {}
    import importlib

    for entry_point in list_submodules(module_):
        module = importlib.import_module(f"{module_.__name__}.{entry_point}")
        module_dir = dir(module)
        if "ENTRY_POINT_NAME" in module_dir and "ENTRY_POINT_DIALOG" in module_dir:
            entry_points_[getattr(module, "ENTRY_POINT_NAME")] = getattr(
                module, "ENTRY_POINT_DIALOG"
            )

    return entry_points_


if __name__ == "__main__":

    def a():
        from exclude import entry_points

        print(get_entry_points(entry_points))

    a()
