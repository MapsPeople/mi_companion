from typing import Generic, ParamSpecArgs, ParamSpecKwargs, Union

__all__ = ["is_union", "is_optional", "get_args", "get_origin"]

try:  # Python >= 3.8
    from typing import Literal, get_args, get_origin

except ImportError:  # Compatibility
    get_args = lambda t: getattr(t, "__args__", ()) if t is not Generic else Generic
    get_origin = lambda t: getattr(t, "__origin__", None)


def is_union(field: Union[ParamSpecArgs, ParamSpecKwargs]) -> bool:
    return get_origin(field) is Union


def is_optional(field: Union[ParamSpecArgs, ParamSpecKwargs]) -> bool:
    return is_union(field) and type(None) in get_args(field)
