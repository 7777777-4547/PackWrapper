from .Logger import Logger
from .Utils import Event

from pathlib import Path
import json

def properties_read(file_path) -> dict:
    
    Event.emit("properties_read_start", file_path)
    
    with open(file_path, 'r', encoding='utf-8') as file:
        properties = json.load(file)
        
    Event.emit("properties_read_end", file_path)
            
    return properties
    

def single_properties_read(file_path: str | Path = "packwrapper.json") -> dict:
    
    try:
        Logger.debug(f"Single properties from the file \"{file_path}\"")
        Logger.info("Reading properties...")
        
        properties = properties_read(file_path)
        
        return properties
        
    
    except Exception:
        Logger.exception(f"Cannot read the properties: \"{file_path}\"")
        return {}


def multiple_properties_read(directory_path: str | Path, file_ext: str = "json") -> dict:
    
        Logger.debug(f"Multiple properties from the directory \"{directory_path}\"")
        Logger.info(f"Reading properties...")
        
        
        directory_path = Path(directory_path) if isinstance(directory_path, str) else directory_path
        

        # Checking directory
        if not any(directory_path.glob(f"*.{file_ext}")):
            Logger.exception(f"Cannot find any properties file in the directory \"{directory_path}\"")
        
        
        properties = {}
        
        for file_path in directory_path.glob(f"*.{file_ext}"):
            if file_path.is_file():
                
                try:
                    properties.update({file_path.name.replace(f".{file_ext}",""): properties_read(file_path)})
                    
                except Exception:
                    Logger.exception(f"Cannot read the properties: \"{file_path}\"")
                
        Logger.debug(json.dumps(properties, indent=4, ensure_ascii=False))
        return properties