from .Logger import Logger, LoggerType
from pathlib import Path

packwrapper_version = "Dev"

"""
Using `PackWrapper.config()` firstly to continuce the next function use.
"""

pack_properties = {}

# PackWrapper Configure
def config(properties: str | Path, debug_mode: bool = False):
    
    # Configure Logger
    Logger.config(filename="packwrapper_debug.log" if debug_mode else "packwrapper.log", 
                  filemode="w", encoding="utf-8", 
                  level=LoggerType.DEBUG if debug_mode else LoggerType.INFO
                  )
    
    Logger.info(f"PackWrapper[{packwrapper_version}]")
    
    # Properties Read
    global pack_properties
    if Path(properties).is_file():
        pack_properties = PropertiesManager.single_properties_read(properties)
    else:
        pack_properties = PropertiesManager.multiple_properties_read(properties)
    
def get_properties():
    return pack_properties


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