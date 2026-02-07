import PackWrapper as PW
from PackWrapper import ScriptSystem

PW.init()

ScriptSystem.init("version_script", PW.get_main_config())
ScriptSystem.run_script("example")

pack_info = PW.get_pack_info()

rp = PW.Resourcepack(**pack_info)
rp.export(export_name = pack_info.get("export_name", None))
rp.package()

ScriptSystem.run_script("example2")