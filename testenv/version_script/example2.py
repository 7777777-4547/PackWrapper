from packwrapper.scriptsystem import Script
from packwrapper.logger import Logger
from packwrapper.utils import EntryPoint, PackWrapperEntryPoint
import packwrapper as PW

import json


config = Script.config()

@EntryPoint("join", PackWrapperEntryPoint.RP_EXPORT_AFTER)
def entry_test():
    Logger.info("Entry test")

entry_test()

Logger.info("Reading config...")
Logger.debug(json.dumps(dict(config), indent=4))
pack_info = config["pack_info"]

with PW.Resourcepack(**pack_info) as rp:
    rp.build()
