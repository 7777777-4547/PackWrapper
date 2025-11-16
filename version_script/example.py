from PackWrapper.ScriptSystem import Script
from PackWrapper.Logger import Logger
import PackWrapper as PW

import json

config = Script.config()

Logger.info("Reading config...")
Logger.debug(json.dumps(dict(config), indent=4))
packinfo = config["pack_info"]

rp = PW.Resourcepack(**packinfo)
rp.export(export_name = packinfo.get("export_name", None))
rp.package()