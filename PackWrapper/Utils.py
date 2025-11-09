from warnings import deprecated
from .Logger import Logger

from urllib.parse import urlparse
from functools import wraps, partial
from pathlib import Path
from typing import Literal, TypeAlias
from enum import Enum, StrEnum, IntEnum
import inspect
import shutil
import httpx


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


class PackWrapperPath(PathEnum):
    
    ROOT = Path("./.packwrapper")
    CACHE = Path(ROOT/"cache")
    EXPORT = Path(ROOT/"export")
    PACKAGE = Path(ROOT/"package")
    GAME = Path(ROOT/"game")
    
    def __init__(self, path):
        path.mkdir(exist_ok=True)


class EventInjector:
    
    #EventType: TypeAlias = Literal['BEFORE','AFTER','REDIRECT']
    
    class EventType(IntEnum):
        BEFORE = 0
        AFTER = 1
        REDIRECT = 2
    
    def create_monitored_method(self, original_method, inject_method, event_type: EventType):
        def monitored_method(*args, **kwargs):
            try:
                match event_type:
                    
                    case self.EventType.BEFORE:
                        inject_method()
                        result = original_method(*args, **kwargs)
                    case self.EventType.AFTER:
                        result = original_method(*args, **kwargs)          
                        inject_method()
                    case self.EventType.REDIRECT:
                        result = inject_method()
                    case _:
                        Logger.exception("Invalid event type", exc_info = ValueError("Invalid event type"))
                        raise
                
                return result
                    
            except Exception as e:
                Logger.exception(f"", exc_info = e)
                
        return monitored_method
        
    
    def __init__(self, cls: object, func_name: str, event_type: EventType):
        self.cls = cls
        self.func_name = func_name
        self.event_type = event_type
        
        self.methods = [name for name, obj in inspect.getmembers(cls, predicate=inspect.isfunction)]
        
        if func_name in self.methods:
            self.func = getattr(cls, func_name)

    def __call__(self, func):
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            
            if callable(getattr(self.cls, self.func_name)):
                func_partial = partial(func, *args, **kwargs)
                monitored_method = self.create_monitored_method(self.func, func_partial, self.event_type)
                setattr(self.cls, self.func_name, monitored_method)
                    
        return wrapper


class Network:
    
    @staticmethod
    def is_url(path_or_url):
        try:
            result = urlparse(path_or_url)
            return bool(result.scheme)
        except Exception:
            return False

    @staticmethod
    def download_file(url, path):
        with httpx.Client(follow_redirects=True) as client:
            with client.stream("GET", url) as response:
                
                try:
                    response.raise_for_status()
                    with open(path, 'wb') as f:
                        for chunk in response.iter_bytes():
                            f.write(chunk)
                    return path
                
                except Exception:
                    Logger.exception(f"Failed to download {url}")


class File:
        
    def __init__(self, path: str):
        
        self.file_path = Path(PackWrapperPath.EXPORT / path.split("/")[-1])
        
        if Network.is_url(path):
            Network.download_file(path, self.file_path)
        else:
            shutil.copy2(path, self.file_path)
    
    def __str__(self):
        return str(self.file_path)


@deprecated("Use EventInjector instead")
class EventType(StrEnum):
    
    CONFIGURED_CHANGE = "configure_status.change"
    CONFIGURED_CHANGED = "configure_status.changed"
    CONFIGURED_GET = "configure_status.get"
    CONFIGURED_CHECK = "configure_status.check"
    
    RESOURCEPACK_CREATE = "resourcepack.create"
    RESOURCEPACK_CREATED = "resourcepack.created"
    RESOURCEPACK_EXPORT = "resourcepack.export"
    RESOURCEPACK_EXPORTING_COPY = "resourcepack.exporting.copy"
    RESOURCEPACK_EXPORTING_COPYED = "resourcepack.exporting.copyed"
    RESOURCEPACK_EXPORTING_DUMP = "resourcepack.exporting.dump"
    RESOURCEPACK_EXPORTING_DUMPED = "resourcepack.exporting.dumped"
    RESOURCEPACK_EXPORTED = "resourcepack.exported"
    RESOURCEPACK_PACKAGE = "resourcepack.package"
    RESOURCEPACK_PACKAGED = "resourcepack.packaged"
    
    @classmethod
    def add_event_type(cls, name, value):
        setattr(cls, name, value)


@deprecated("Use EventInjector instead")
class Event:
    
    _subscribers = {}
    events = []
    
    @classmethod
    def subscribe(cls, event_type: EventType, callback):
        Logger.debug(f"Subscribing to event \"{event_type}\" and callback \"{callback}\"")

        cls._subscribers.setdefault(event_type, []).append(callback)
    
    @classmethod
    def unsubscribe(cls, event_type: EventType, callback):
        Logger.debug(f"Unsubscribing from event \"{event_type}\" and callback \"{callback}\"")

        if event_type in cls._subscribers:
            cls._subscribers[event_type].remove(callback)
                    
    @classmethod
    def emit(cls, event_type: EventType):
        Logger.debug(f"Event \"{event_type}\" emitted")
        cls.events.append(event_type)

        for callback in cls._subscribers.get(event_type, []):
            try:
                callback()
            except Exception as e:
                Logger.exception(f"Event callback error: {e}")

    @classmethod
    def emit_withdata(cls, event_type: EventType, data=None):
        Logger.debug(f"Event \"{event_type}\" emitted with data: \"{data}\"")

        for callback in cls._subscribers.get(event_type, []):
            try:
                callback(data)
            except Exception as e:
                Logger.exception(f"Event callback error: {e}")