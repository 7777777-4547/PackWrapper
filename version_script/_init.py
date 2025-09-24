import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


from PackWrapper import PropertiesManager

def config_read(file_path):
    PropertiesManager.properties_read(os.path.join(os.path.dirname(__file__), file_path))
    
def get_config():
    args = sys.argv[1:]
    if 0 < len(args):
        return args[0]
    raise ValueError(f"No argument provided, it needs one")