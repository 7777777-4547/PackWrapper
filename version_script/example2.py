import _init

from PackWrapper.ScriptSystem import script_logger_config
from PackWrapper.Logger import Logger
import PackWrapper as PW

import json



config = json.loads(_init.get_config())
script_logger_config(config.get("packwrapper", {}).get("debug_mode",False))

@PW.EventInjector(PW.Resourcepack, "package", PW.EventInjector.EventType.BEFORE)
def test():
    Logger.info("injector test")

test()


Logger.info("Reading config...")
Logger.debug(json.dumps(config, indent=4))
packinfo = config["pack_info"]

rp = PW.Resourcepack(**packinfo)
rp.export(export_name = packinfo.get("export_name", None))
rp.package()

