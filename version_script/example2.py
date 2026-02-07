from PackWrapper.ScriptSystem import Script
from PackWrapper.Logger import Logger
from PackWrapper.Utils import EntryPoint, PackWrapperEntryPoint
import PackWrapper as PW

import json


config = Script.config()

@EntryPoint("join", PackWrapperEntryPoint.RP_EXPORT_AFTER)
def entry_test():
    Logger.info("Entry test")

entry_test()

Logger.info("Reading config...")
Logger.debug(json.dumps(dict(config), indent=4))
packinfo = config["pack_info"]

rp = PW.Resourcepack(**packinfo)
rp.export(export_name = packinfo.get("export_name", None))
rp.package()