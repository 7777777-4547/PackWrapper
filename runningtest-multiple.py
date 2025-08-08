from PackWrapper import *

config("propertiestest_multiple",debug_mode=True)

for key in get_properties().keys():
    Resourcepack(**get_properties()[key]).export(export_name = get_properties()[key]["export_name"])