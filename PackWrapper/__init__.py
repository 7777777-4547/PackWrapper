from .Resourcepack import Resourcepack
from .HashCalculate import hashc_file
from .Logger import Logger, LoggerType
from .Utils import Event, EventInjector
from .PropertiesManager import properties_read
from . import StatusChecker
from . import ScriptSystem

import copy

packwrapper_version = "Dev"

"""
Using `PackWrapper.init()` firstly to continuce the next function use.
"""

MAIN_PROPERTIES = {}

# PackWrapper Configure
def init():
    
    global MAIN_PROPERTIES
    
    MAIN_PROPERTIES = properties_read("packwrapper")
    debug_mode = MAIN_PROPERTIES.get("packwrapper", {}).get("debug_mode", False)
    
    # Configure Logger
    Logger.config(filename="packwrapper_debug.log" if debug_mode else "packwrapper.log", 
                  filemode="w", encoding="utf-8", 
                  level=LoggerType.DEBUG if debug_mode else LoggerType.INFO
                  )
    
    Logger.info(f"PackWrapper[{packwrapper_version}]")

    if StatusChecker.get_configure_status() is False:
        StatusChecker.change_configure_status(True)
    else:
        Logger.exception("PackWrapper is already configured. Please don't configure it again.")
        
    
def get_properties_main():
    return copy.deepcopy(MAIN_PROPERTIES)

def get_packinfo():
    return copy.deepcopy(MAIN_PROPERTIES["pack_info"])


__all__ = [
    "properties_read",
    "get_properties_main",
    
    "Event",
    "Logger",
    "Resourcepack",
    "ScriptSystem",
    
    "init",
    "hashc_file"
]