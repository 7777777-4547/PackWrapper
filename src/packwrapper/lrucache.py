from warnings import deprecated

from .logger import Logger

from collections import OrderedDict
from functools import lru_cache
from pathlib import Path
from typing import IO, Any
from PIL import Image
from abc import ABC, abstractmethod
import threading
import io


CACHE: OrderedDict[Path, bytes] = OrderedDict()
CACHE_SIZE_MAX = 32 * 1024 * 1024
CACHE_SIZE_CURRENT = 0

@deprecated("Performance Problem, directly use default I/O methods instead")
class LRUCache(ABC):
    _lock = threading.RLock()

    @classmethod
    @lru_cache(8192)
    def _get_file_size(cls, file: Path) -> int:
        return file.stat().st_size

    @classmethod
    @abstractmethod
    def get(cls, file: Path) -> Any: ...

    @classmethod
    def clear(cls) -> None:
        with cls._lock:
            global CACHE
            CACHE.clear()
            global CACHE_SIZE_CURRENT
            CACHE_SIZE_CURRENT = 0

    @classmethod
    def get_current_size(cls) -> int:  # Bytes
        """
        Returns the current size of the cache (in Bytes)
        """
        with cls._lock:
            return CACHE_SIZE_CURRENT

    @classmethod
    def get_max_size(cls) -> int:  # Bytes
        """
        Returns the maximum size of the cache (in Bytes)
        """
        with cls._lock:
            return CACHE_SIZE_MAX

    @classmethod
    def set_max_size(cls, size: float):  # MB
        """
        Sets the maximum size of the cache

        Args:
            size: Maximum size in MB (will be converted to Bytes internally)
        """
        with cls._lock:
            global CACHE, CACHE_SIZE_CURRENT, CACHE_SIZE_MAX
            CACHE_SIZE_MAX = int(size * 1024 * 1024)

            while CACHE_SIZE_CURRENT > CACHE_SIZE_MAX:
                _, old_data = CACHE.popitem(last=False)
                old_size = len(old_data)
                CACHE_SIZE_CURRENT -= old_size


@deprecated("Performance Problem, directly use default I/O methods instead")
class FileLRUCache(LRUCache):
    @classmethod
    def get(cls, file: Path) -> IO[bytes]:
        global CACHE, CACHE_SIZE_CURRENT, CACHE_SIZE_MAX

        file = file.absolute()

        if not file.exists():
            Logger.error(f'File "{file}" not found', exc_info=FileNotFoundError)

        with cls._lock:
            if file in CACHE:
                CACHE.move_to_end(file)
                return io.BytesIO(CACHE[file])

            file_size = cls._get_file_size(file)

            with file.open("rb") as f:
                data = f.read()

                if file_size > CACHE_SIZE_MAX:
                    return io.BytesIO(data)

                while CACHE_SIZE_CURRENT + file_size > CACHE_SIZE_MAX:
                    _, old_data = CACHE.popitem(last=False)
                    old_size = len(old_data)
                    CACHE_SIZE_CURRENT -= old_size

                if file_size <= CACHE_SIZE_MAX:
                    CACHE[file] = data
                    CACHE_SIZE_CURRENT += file_size

            return io.BytesIO(data)


@deprecated("Performance Problem, directly use default I/O methods instead")
class ImageLRUCache(LRUCache):
    @classmethod
    def get(cls, file: Path) -> Image.Image:
        return Image.open(FileLRUCache.get(file))