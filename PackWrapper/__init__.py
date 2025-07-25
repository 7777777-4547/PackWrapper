from .Logger import Logger, LoggerType
from . import StatusChecker

from pathlib import Path

packwrapper_version = "Dev"

"""
Using `PackWrapper.config()` firstly to continuce the next function use.
"""

PACK_PROPERTIES = {}

# PackWrapper Configure
def config(properties: str | Path, debug_mode: bool = False):
    
    global PACK_PROPERTIES
    
    if StatusChecker.get_configure_status() is False:
        StatusChecker.change_configure_status(True)
    else:
        Logger.exception("PackWrapper is already configured. Please don't configure it again.")
    
    # Configure Logger
    Logger.config(filename="packwrapper_debug.log" if debug_mode else "packwrapper.log", 
                  filemode="w", encoding="utf-8", 
                  level=LoggerType.DEBUG if debug_mode else LoggerType.INFO
                  )
    
    Logger.info(f"PackWrapper[{packwrapper_version}]")
    
    # Properties Read
    if Path(properties).is_file():
        PACK_PROPERTIES = PropertiesManager.single_properties_read(properties)
    else:
        PACK_PROPERTIES = PropertiesManager.multiple_properties_read(properties)
        
    
def get_properties():
    return PACK_PROPERTIES


from .Resourcepack import Resourcepack, ResourcepackAuto
from . import PropertiesManager
from .HashCalculate import hashc_file, async_hashc_file

__all__ = [
    "get_properties",
    
    "Logger",
    "Resourcepack",
    "ResourcepackAuto",
    
    "config",
    "hashc_file",
    "async_hashc_file"
]