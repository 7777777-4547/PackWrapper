from .StatusChecker import change_configure_status
from .PropertiesManager import properties_read
from .Logger import Logger, LoggerType

from pathlib import Path
import json
import sys



SCRIPT_DIR: Path | str
_main_properties: dict

def get_properties_main():
    global _main_properties
    return _main_properties


def init(script_dir: Path | str, main_properties: dict):
    global SCRIPT_DIR
    SCRIPT_DIR = script_dir
    global _main_properties
    _main_properties = main_properties
    
    Logger.info("[ScriptSystem] ScriptSystem initialized.")



def script_logger_config(debug_mode = False):

    Logger.config(
        filename = "packwrapper_script_debug.log",
        filemode = "w",
        level = LoggerType.DEBUG,
        format = "[%(asctime)s][%(threadName)s/%(levelname)s]: [ScriptSystem] %(message)s", 
        datefmt = "%Y/%m/%d|%H:%M:%S"
    ) if debug_mode else Logger.config(
        filename = "packwrapper_script.log",
        filemode = "w",
        level = LoggerType.INFO,
        format = "[%(asctime)s][%(threadName)s/%(levelname)s]: [ScriptSystem] %(message)s", 
        datefmt = "%Y/%m/%d|%H:%M:%S"
    )
    
    change_configure_status(True)

def merge_properties(script_config_filename: str | Path):
    
    script_config = get_properties_main()
    
    script_config_original = properties_read(script_config_filename)
    
    for key, value in script_config_original.items():
        if isinstance(value, dict):
            for subkey, subvalue in value.items():
                script_config[key][subkey] = subvalue
        else:
            script_config[key] = value
    
    return script_config

    
def run_script(script_name: str | Path, timeout: int = 5):
        
    script_filename = Path(SCRIPT_DIR, f"{script_name}.py")
    script_config_filename = Path(SCRIPT_DIR, f"{script_name}.json")
    
    if script_filename.exists() and script_config_filename.exists():
        
        # Merge config
        Logger.info(f"[ScriptSystem] Merging config for script \"{script_name}\"...")

        script_config = merge_properties(script_config_filename)
    
        # Run script
        Logger.info(f"[ScriptSystem] Running script \"{script_name}\"...")
        
        script_config = json.dumps(script_config)
        
        import subprocess
        
        cmd = [sys.executable, script_filename, script_config]
                
        try:
            subprocess.run(cmd, timeout=timeout)
            Logger.info(f"[ScriptSystem] Script \"{script_name}\" finished.")
            
        except subprocess.TimeoutExpired:
            Logger.exception(f"[ScriptSystem] Script \"{script_name}\" timed out.")
        except Exception:
            Logger.exception(f"[ScriptSystem] Script \"{script_name}\" failed.")

    else:
        Logger.exception(f"[ScriptSystem] Script \"{script_name}\" not found or not configured correctly.")

