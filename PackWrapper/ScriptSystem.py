from .StatusChecker import change_configure_status
from .PropertiesManager import properties_read
from .Logger import Logger, LoggerType

from pathlib import Path
import subprocess
import inspect
import copy
import json
import sys


SCRIPT_DIR: Path | str
MAIN_PROPERTIES: dict = {}

def get_properties_main():
    return copy.deepcopy(MAIN_PROPERTIES)


@Logger.ID("ScriptSystem")
def init(script_dir: Path | str, main_properties: dict):
    global SCRIPT_DIR
    SCRIPT_DIR = script_dir
    global MAIN_PROPERTIES
    MAIN_PROPERTIES = main_properties
    
    Logger.info("ScriptSystem initialized.")



def script_logger_config(debug_mode = False):
    
    frame = inspect.currentframe()
    if frame is None: 
        Logger.exception("No frame can be called back.")
        raise
    else:
        if frame.f_back is None: 
            Logger.exception("No frame can be called back.")
            raise
        else:
            caller_filename = Path(frame.f_back.f_code.co_filename).stem
    
    Logger.ID.set(f"ScriptSystem/{caller_filename}")

    Logger.config(
        filename = "packwrapper_script_debug.log",
        filemode = "w",
        level = LoggerType.DEBUG
    ) if debug_mode else Logger.config(
        filename = "packwrapper_script.log",
        filemode = "w",
        level = LoggerType.INFO
    )
    
    change_configure_status(True)

def merge_properties(script_config_filename: str | Path):
    
    script_config = get_properties_main()
    
    script_config_original = properties_read(script_config_filename)
    
    for key, value in script_config_original.items():
        if isinstance(value, dict) and (key in script_config):
            for subkey, subvalue in value.items():
                script_config[key][subkey] = subvalue
        else:
            script_config[key] = value
    
    return script_config

    
@Logger.ID("ScriptSystem")
def run_script(script_name: str | Path, timeout: float | None = None):
        
    script_filename = Path(SCRIPT_DIR, f"{script_name}.py")
    script_config_filename = Path(SCRIPT_DIR, f"{script_name}.json")
    
    is_debug_mode = sys.gettrace() is not None
    
    if script_filename.exists() and script_config_filename.exists():
        
        # Merge config
        Logger.info(f"Merging config for script \"{script_name}\"...")

        script_config = merge_properties(script_config_filename)
    
        # Run script
        Logger.info(f"Running script \"{script_name}\"...")
        
        script_config = json.dumps(script_config)
        
        cmd = [sys.executable, script_filename, script_config]
                
        try:
            subprocess.run(cmd, timeout = timeout if not is_debug_mode else None)
            Logger.info(f"Script \"{script_name}\" finished.")
            
            
        except subprocess.TimeoutExpired:
            Logger.exception(f"Script \"{script_name}\" timed out.")
            
            
        except Exception:
            Logger.exception(f"Script \"{script_name}\" failed.")
            

    else:
        Logger.exception(f"Script \"{script_name}\" not found or not configured correctly.")
        

