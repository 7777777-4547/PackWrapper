import packwrapper as PW
from packwrapper import ScriptSystem

PW.init()

pack_info = PW.get_pack_info()

with PW.Resourcepack(**pack_info) as rp:
    rp.build()

ScriptSystem.init("version_script", PW.get_main_config(), "scripts")
ScriptSystem.run_script("example")
ScriptSystem.run_script("example2")
ScriptSystem.run_script_multiple(["example3"])