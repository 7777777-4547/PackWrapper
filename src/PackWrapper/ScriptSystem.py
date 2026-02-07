from PackWrapper.Utils import PackWrapperPath
from .StatusChecker import change_configure_status
from .Config import ConfigManager
from .Logger import Logger, LoggerType

from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path
from types import FrameType, MappingProxyType
import subprocess
import inspect
import copy
import json
import time
import sys
import os


SCRIPT_DIR: Path | str
MAIN_CONFIG: dict = {}
MULTI_TREAD = False


def get_main_config():
    return copy.deepcopy(MAIN_CONFIG)


@Logger.ID("ScriptSystem")
def init(script_dir: Path | str, main_properties: dict):
    global SCRIPT_DIR
    SCRIPT_DIR = script_dir
    global MAIN_CONFIG
    MAIN_CONFIG = main_properties

    Logger.info("ScriptSystem initialized.")


def merge_config(script_config_filename_without_suffix: str | Path) -> dict:

    script_config = get_main_config()

    try:
        script_config_original = ConfigManager.read_config(
            script_config_filename_without_suffix
        )
    except FileNotFoundError:
        Logger.exception(
            f'Script config "{script_config_filename_without_suffix}" not found.'
        )
        raise

    for key, value in script_config_original.items():
        if isinstance(value, dict) and (key in script_config):
            for subkey, subvalue in value.items():
                script_config[key][subkey] = subvalue
        else:
            script_config[key] = value

    ConfigManager.validate_config(script_config)

    return script_config


@Logger.ID("ScriptSystem")
def run_script(script_name: str | Path, timeout: float | None = None, multi_thread=False):

    def is_debugging():
        if sys.gettrace() is not None:
            return True

        if "pydevd" in sys.modules:
            return True

        if any("debugpy" in arg for arg in sys.argv):
            return True

        return False

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    script_filename = Path(SCRIPT_DIR, f"{script_name}.py")
    # script_config_filename = Path(SCRIPT_DIR, f"{script_name}.json")

    is_debug_mode = is_debugging()

    if script_filename.exists():
        # Merge config
        Logger.info(f'Merging config for script "{script_name}"...')

        script_config = merge_config(Path(SCRIPT_DIR, script_name))

        # Run script
        Logger.info(f'Running script "{script_name}"...')

        script_config = json.dumps(script_config)

        cmd = [sys.executable, script_filename, script_config, str(multi_thread)]

        try:
            start_time = time.perf_counter()
            subprocess.run(cmd, timeout=timeout if not is_debug_mode else None)
            end_time = time.perf_counter()
            spend_time = end_time - start_time
            spend_time = f"{spend_time:.2f}s" if spend_time > 10 else f"{spend_time*1000:.0f}ms"
            Logger.info(f'Script "{script_name}" finished. ({spend_time})')

        except subprocess.TimeoutExpired:
            Logger.exception(f'Script "{script_name}" timed out.')

        except Exception:
            Logger.exception(f'Script "{script_name}" failed.')

    else:
        Logger.exception(f'Script "{script_name}" not found.')


@Logger.ID("ScriptSystem")
def run_script_multiple(scripts: list[str]):

    Logger.info("Running multiple scripts...")

    _run_script = partial(run_script, multi_thread=True)

    start_time = time.perf_counter()
    with ThreadPoolExecutor() as executor:
        executor.map(_run_script, scripts)
    end_time = time.perf_counter()
    spend_time = end_time - start_time
    spend_time = f"{spend_time:.2f}s" if spend_time > 10 else f"{spend_time*1000:.0f}ms"
    Logger.info(f"All scripts finished. ({spend_time})")

class Script:
    @staticmethod
    def config():

        _config = json.loads(Script._get_config())

        Script._script_logger_config(
            frame=inspect.currentframe(),
            debug_mode=_config.get("packwrapper", {}).get("debug_mode", False),
            multi_thread=Script._get_multi_thread_status(),
        )

        return MappingProxyType(_config)

    @staticmethod
    def _get_config():
        args = sys.argv[1:]
        if 0 < len(args):
            return args[0]
        raise ValueError("No argument provided, it needs one")

    @staticmethod
    def _get_multi_thread_status() -> bool:
        args = sys.argv[1:]
        if len(args) >= 2:
            return bool(args[1])
        raise ValueError("No second argument provided, it needs one")

    @staticmethod
    def _script_logger_config(
        frame: FrameType | None, debug_mode=False, multi_thread=False
    ):
        script_log_dir = Path(PackWrapperPath.LOG / "scripts")
        script_log_dir.mkdir(parents=True, exist_ok=True)

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
            filename=f"scripts/{caller_filename}_debug.log",
            filemode="w",
            level=LoggerType.DEBUG,
            multi_thread=multi_thread,
        ) if debug_mode else Logger.config(
            filename=f"scripts/{caller_filename}.log",
            filemode="w",
            level=LoggerType.INFO,
            multi_thread=multi_thread,
        )

        change_configure_status(True)
