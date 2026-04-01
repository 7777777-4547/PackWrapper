from packwrapper.logger import Logger

from typing import TypeVar, ParamSpec, Callable
from abc import ABC, abstractmethod
from functools import wraps

P = ParamSpec("P")
R = TypeVar("R")


def plugin_logger(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        if args and hasattr(args[0], "name"):
            Logger.ExtID.set(getattr(args[0], "name"))
        else:
            Logger.ExtID.set("Unknown")
        try:
            return func(*args, **kwargs)
        finally:
            Logger.ExtID.reset()

    return wrapper


class Plugin(ABC):
    """
    A plugin for PackWrapper content.
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "name"):
            cls._name = cls.__name__

        original_init = cls.__init__

        def wrapped_init(self, *args, **kwargs):
            @plugin_logger
            def call_init():
                return original_init(self, *args, **kwargs)

            call_init()

        cls.__init__ = wrapped_init

    def __init__(self, name: str | None = None):
        self._name = name if name is not None else type(self).__name__

    @property
    def name(self) -> str:
        return self._name

    @plugin_logger
    @abstractmethod
    def __call__(self): ...

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name='{self.name}')"
