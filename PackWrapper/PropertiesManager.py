from pathlib import Path
import json5
import json


PROPERTIES_SUFFIX = [".json", ".json5"]

def suffix_with(file_path_without_suffix: str | Path) -> Path:
    
    for suffix in PROPERTIES_SUFFIX:
        
        if Path(file_path_without_suffix).with_suffix(suffix).exists():
            file_path = Path(file_path_without_suffix).with_suffix(suffix)
            return file_path
    
    else:
        raise Exception(f"Cannot find the properties file: \"{file_path_without_suffix}\"")    


def properties_read(file_path_without_suffix) -> dict:
    
    file_path = suffix_with(file_path_without_suffix)
        
    file_suffix = Path(file_path).suffix
    
    match file_suffix:
        case ".json":
            return properties_read_json(file_path)
        case ".json5":
            return properties_read_json5(file_path)
        case _:
            raise Exception(f"Unknown properties file format: \"{file_path}\"")


def properties_read_json(file_path) -> dict:
    
    try:    
        with open(file_path, 'r', encoding='utf-8') as file:
            properties = json.load(file)
                            
        return properties
    
    except Exception:
        
        raise Exception(f"Cannot read the properties: \"{file_path}\"")


def properties_read_json5(file_path) -> dict:
    
    try:    
        with open(file_path, 'r', encoding='utf-8') as file:
            properties = json5.load(file)
                            
        return dict(properties)
    
    except Exception:
        
        raise Exception(f"Cannot read the properties: \"{file_path}\"")