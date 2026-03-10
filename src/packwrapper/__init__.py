from .lrucache import FileLRUCache, ImageLRUCache
from .content import Resourcepack
from .logger import Logger, LoggerType
from .config import ConfigManager
from .utils import HashCalculator
from . import scriptsystem as ScriptSystem

import toml
import copy


try:
    from importlib.metadata import version, PackageNotFoundError

    try:
        packwrapper_version = version("PackWrapper")
    except PackageNotFoundError:
        packwrapper_version = "Dev"

except ImportError:
    packwrapper_version = "Dev"

"""
Using `PackWrapper.init()` firstly to continuce the next function use.
"""

MAIN_CONFIG: dict = {}


# PackWrapper Configure
def init(main_config_path: str = "packwrapper"):

    global MAIN_CONFIG

    MAIN_CONFIG = ConfigManager.read_config(main_config_path)
    debug_mode = MAIN_CONFIG.get("packwrapper", {}).get("debug_mode", False)

    # Configure Logger
    Logger.config(
        filename="packwrapper_debug.log" if debug_mode else "packwrapper.log",
        filemode="w",
        encoding="utf-8",
        level=LoggerType.DEBUG if debug_mode else LoggerType.INFO,
    )

    Logger.info(f"PackWrapper[{packwrapper_version}]")


def get_main_config() -> dict:
    return copy.deepcopy(MAIN_CONFIG)


def get_pack_info() -> dict:
    return copy.deepcopy(MAIN_CONFIG.get("pack_info", {}))


def logout_config_formatted(config: dict):
    raw_output = toml.dumps(config)
    split_output = raw_output.split("\n")
    for line in split_output:
        if line.startswith("[") and line.endswith("]"):
            Logger.info(line)
        else:
            Logger.info(" " * 4 + line)


__all__ = [
    "Resourcepack",
    "HashCalculator",
    "FileLRUCache",
    "ImageLRUCache",
    "ScriptSystem",
    "Logger",
    "LoggerType",
]
