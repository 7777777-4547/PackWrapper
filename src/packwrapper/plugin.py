from packwrapper.logger import Logger

from abc import ABC, abstractmethod
from typing import TypeVar, cast

T = TypeVar('T', bound='Plugin')

def plugin_logger(name: str | None = None):

    def decorate(cls: type[T]) -> type[T]:

        nonlocal name

        if name is None:
            name = cls._get_name()

        _logger_ext_id = Logger.ExtID(name)

        for attr_name in dir(cls):
            if attr_name == "_get_name":
                continue

            if attr_name.startswith("__") and attr_name.endswith("__"):
                if attr_name != "__init__":
                    continue

            original_attr = cls.__dict__.get(attr_name)
            if original_attr is None:
                continue

            if isinstance(original_attr, staticmethod):
                continue

            attr = getattr(cls, attr_name)
            if callable(attr):
                setattr(cls, attr_name, _logger_ext_id(attr))
        return cast(type[T], cls)

    return decorate


@plugin_logger()
class Plugin(ABC):
    """
    A plugin for PackWrapper content.
    """

    @classmethod
    def _get_name(cls) -> str:
        return cls.__name__

    def __init__(self): ...

    @abstractmethod
    def __call__(self): ...

    @property
    def name(self):
        return self._get_name()
