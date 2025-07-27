from .Logger import Logger
from .PathEnum import PackWrapper

from urllib.parse import urlparse
from pathlib import Path
import shutil
import httpx


class Network:
    
    @staticmethod
    def is_url(path_or_url):
        try:
            result = urlparse(path_or_url)
            return bool(result.scheme)
        except Exception:
            return False

    @staticmethod
    def download_file(url, path):
        with httpx.Client() as client:
            with client.stream("GET", url) as response:
                
                try:
                    response.raise_for_status()
                    with open(path, 'wb') as f:
                        for chunk in response.iter_bytes():
                            f.write(chunk)
                    return path
                
                except Exception:
                    Logger.exception(f"Failed to download {url}")


class File:
        
    def __init__(self, path: str):
        
        file_path = Path(PackWrapper.CACHE / path.split("/")[-1])
        
        if Network.is_url(path):
            Network.download_file(path, file_path)
        else:
            shutil.copy2(path, file_path)
            
        return file_path

    
