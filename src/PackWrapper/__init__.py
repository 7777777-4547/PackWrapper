from .Resourcepack import Resourcepack
from .Logger import Logger, LoggerType
from .Utils import HashCalculator
from .Config import ConfigManager
from . import StatusChecker
from . import ScriptSystem

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
def init():

    global MAIN_CONFIG

    MAIN_CONFIG = ConfigManager.read_config("packwrapper")
    debug_mode = MAIN_CONFIG.get("packwrapper", {}).get("debug_mode", False)

    # Configure Logger
    Logger.config(
        filename="packwrapper_debug.log" if debug_mode else "packwrapper.log",
        filemode="w",
        encoding="utf-8",
        level=LoggerType.DEBUG if debug_mode else LoggerType.INFO,
    )

    Logger.info(f"PackWrapper[{packwrapper_version}]")

    if StatusChecker.get_configure_status() is False:
        StatusChecker.change_configure_status(True)
    else:
        Logger.exception(
            "PackWrapper is already configured. Please don't configure it again."
        )


def get_main_config() -> dict:
    return copy.deepcopy(MAIN_CONFIG)


def get_pack_info() -> dict:
    return copy.deepcopy(MAIN_CONFIG.get("pack_info", {}))


__all__ = [
    "get_main_config",
    "init",
    "HashCalculator",
    "Resourcepack",
    "ScriptSystem",
    "Logger",
]
