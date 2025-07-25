from PackWrapper import *

config("propertiestest_multiple",debug_mode=True)

for key in get_properties().keys():
    ResourcepackAuto(get_properties()[key]).export()