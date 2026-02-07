from .Logger import Logger

from functools import wraps
from pathlib import Path
from typing import Literal, TypeAlias, Callable
from enum import Enum, StrEnum
import hashlib


class PathEnum(Enum):
    def __new__(cls, path: str | Path) -> "PathEnum":
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
    CACHE = Path(ROOT / "cache")
    EXPORT = Path(ROOT / "export")
    PACKAGE = Path(ROOT / "package")
    GAME = Path(ROOT / "game")

    LOG = Path(ROOT / "log")

    def __init__(self, path: Path):
        path.mkdir(exist_ok=True)


class HashCalculator:
    HashCalculateType: TypeAlias = Literal[
        "md5",
        "sha1",
        "sha224",
        "sha256",
        "sha384",
        "sha512",
        "blake2b",
        "blake2s",
        "sha3_224",
        "sha3_256",
        "sha3_384",
        "sha3_512",
        "shake_128",
        "shake_256",
    ]

    @staticmethod
    def hashc_file(
        file_path: str, hash_type: HashCalculateType = "sha256"
    ) -> str | None:

        try:
            hash_obj = hashlib.new(hash_type)

            with open(file_path, "rb") as file:
                for chunk in iter(lambda: file.read(4096), b""):
                    hash_obj.update(chunk)

            return hash_obj.hexdigest()

        except Exception:
            Logger.exception(f'Cannot calculate the hash: "{file_path}"')


class EntryPoint:
    _entry_list: dict[str, list[Callable | tuple[Callable, tuple, dict]]] = {}

    @classmethod
    def join(cls, name: str, func: Callable, *args, **kwargs):
        if args or kwargs:
            cls._entry_list.setdefault(name, []).append((func, args, kwargs))
            Logger.debug(f"EntryPoint \"{name}\" joined: {func.__name__}")
        else:
            cls._entry_list.setdefault(name, []).append(func)
            Logger.debug(f"EntryPoint \"{name}\" joined: {func.__name__}")

    @classmethod
    def create(cls, name: str):
        Logger.debug(f"EntryPoint \"{name}\" created")
        func_list = cls._entry_list.get(name)
        if func_list is None:
            return

        for item in func_list:
            try:
                if callable(item):
                    func = item
                    func()
                else:
                    func, args, kwargs = item
                    func(*args, **kwargs)
            except Exception as e:
                Logger.exception(f"EntryPoint \"{name}\" failed: {e}")

    def __init__(self, type_: Literal["join", "create"], name: str):
        self.type_ = type_
        self.name = name

    def __call__(self, func: Callable):

        @wraps(func)
        def wrapper(*args, **kwargs):
            if self.type_ == "join":
                EntryPoint.join(self.name, func, *args, **kwargs)
            elif self.type_ == "create":
                EntryPoint.create(f"{self.name}_before")
                func(*args, **kwargs)
                EntryPoint.create(f"{self.name}_after")
            else:
                raise ValueError(f"Invalid entry point type: '{self.type_}'")
        return wrapper


class PackWrapperEntryPoint(StrEnum):
    RP_EXPORT_BEFORE = "rp_export_before"
    RP_EXPORT_COPY_BEFORE = "rp_export_copy_before"
    RP_EXPORT_COPY_AFTER = "rp_export_copy_after"
    RP_EXPORT_AFTER = "rp_export_after"
    RP_PACKAGE_BEFORE = "rp_package_before"
    RP_PACKAGE_AFTER = "rp_package_after"
