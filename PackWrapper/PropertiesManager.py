import json

def properties_read(file_path) -> dict:
    
    try:    
        with open(file_path, 'r', encoding='utf-8') as file:
            properties = json.load(file)
                            
        return properties
    
    except Exception:
        
        raise Exception(f"Cannot read the properties: \"{file_path}\"")