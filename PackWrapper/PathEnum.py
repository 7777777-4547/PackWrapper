from enum import Enum
from pathlib import Path

class PathEnum(Enum):
    def __new__(cls, path: str | Path) -> 'PathEnum':
        obj = object.__new__(cls)
        obj._value_ = Path(path)
        return obj
    def __getattr__(self, name: str):
        return getattr(self._value_, name)
    def __str__(self) -> str:
        return str(self._value_)
    def __truediv__(self, other) -> Path:
        return self._value_ / other


class PackWrapper(PathEnum):
    
    ROOT = Path("./.packwrapper")
    CACHE = Path(ROOT/"cache")
    GAME = Path(ROOT/"game")
    EXPORT = Path(ROOT/"export")
    
    def __init__(self, path):
        path.mkdir(exist_ok=True)