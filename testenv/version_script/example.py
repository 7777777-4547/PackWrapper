from packwrapper.scriptsystem import Script
from packwrapper.logger import Logger
import packwrapper as PW

import json

config = Script.config()

Logger.info("Reading config...")
Logger.debug(json.dumps(dict(config), indent=4))
pack_info = config["pack_info"]

with PW.Resourcepack(**pack_info) as rp:
    rp.build()