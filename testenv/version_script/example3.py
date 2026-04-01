from packwrapper.scriptsystem import Script
from packwrapper.logger import Logger
from packwrapper.utils import EntryPoint
import packwrapper as PW


config = Script.config()

@EntryPoint("join", PW.content.ContentEntryPoint.EXPORT_COPY, EntryPoint.At.AFTER)
def entry_test():
    Logger.info("Entry test")

entry_test()

Logger.info("Reading config...")
PW.logout_config_formatted(dict(config))
pack_info = config["pack_info"]

with PW.Resourcepack(**pack_info) as rp:
    rp.build()
