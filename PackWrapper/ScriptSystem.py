from .StatusChecker import change_configure_status
from .PropertiesManager import properties_read
from .Logger import Logger, LoggerType

from pathlib import Path
from types import MappingProxyType
import subprocess
import inspect
import copy
import json
import sys
import os


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



def merge_properties(script_config_filename_without_suffix: str | Path):
    
    script_config = get_properties_main()
    
    try:
        script_config_original = properties_read(script_config_filename_without_suffix)
    except FileNotFoundError:
        Logger.exception(f"Script config \"{script_config_filename_without_suffix}\" not found.")
        raise
    
    for key, value in script_config_original.items():
        if isinstance(value, dict) and (key in script_config):
            for subkey, subvalue in value.items():
                script_config[key][subkey] = subvalue
        else:
            script_config[key] = value
    
    return script_config

    
@Logger.ID("ScriptSystem")
def run_script(script_name: str | Path, timeout: float | None = None):

    def is_debugging():
        # 检查是否设置了跟踪函数
        if sys.gettrace() is not None:
            return True
        
        # 检查是否在 PyCharm 或类似 IDE 中运行
        if 'pydevd' in sys.modules:
            return True
            
        # 检查是否在 VS Code 中调试
        if any('debugpy' in arg for arg in sys.argv):
            return True
            
        return False
    
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    script_filename = Path(SCRIPT_DIR, f"{script_name}.py")
    script_config_filename = Path(SCRIPT_DIR, f"{script_name}.json")
    
    is_debug_mode = is_debugging()
    
    if script_filename.exists():
        
        # Merge config
        Logger.info(f"Merging config for script \"{script_name}\"...")

        script_config = merge_properties(Path(SCRIPT_DIR, script_name))
    
        # Run script
        Logger.info(f"Running script \"{script_name}\"...")
        
        script_config = json.dumps(script_config)
        
        cmd = [sys.executable, script_filename, script_config]
        
        env = os.environ.copy()
        python_path = env.get('PYTHONPATH', '')
        if python_path:
            env['PYTHONPATH'] = project_root + os.pathsep + python_path
        else:
            env['PYTHONPATH'] = project_root
                
        try:
            subprocess.run(cmd, timeout = timeout if not is_debug_mode else None, cwd=project_root, env=env)
            Logger.info(f"Script \"{script_name}\" finished.")
            
            
        except subprocess.TimeoutExpired:
            Logger.exception(f"Script \"{script_name}\" timed out.")
            
            
        except Exception:
            Logger.exception(f"Script \"{script_name}\" failed.")
            

    else:
        Logger.exception(f"Script \"{script_name}\" not found.")
        

class Script:
        
    @staticmethod
    def config():
        
        _config = json.loads(Script._get_config())
        
        Script._script_logger_config(_config.get("packwrapper", {}).get("debug_mode",False))
        
        return MappingProxyType(_config)
    
    @staticmethod
    def _get_config():
        args = sys.argv[1:]
        if 0 < len(args):
            return args[0]
        raise ValueError(f"No argument provided, it needs one")
    
    @staticmethod
    def _script_logger_config(debug_mode = False):
    
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
