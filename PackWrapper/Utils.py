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
        with httpx.Client(follow_redirects=True) as client:
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
        
        file_path = Path(PackWrapper.EXPORT / path.split("/")[-1])
        
        if Network.is_url(path):
            Network.download_file(path, file_path)
        else:
            shutil.copy2(path, file_path)
            
        return file_path

    
class Event:
    
    _subscribers = {}
    
    @classmethod
    def subscribe(cls, event_type, callback):
        Logger.debug(f"Subscribing to event \"{event_type}\" and callback \"{callback}\"")

        cls._subscribers.setdefault(event_type, []).append(callback)
    
    @classmethod
    def unsubscribe(cls, event_type, callback):
        Logger.debug(f"Unsubscribing from event \"{event_type}\" and callback \"{callback}\"")

        if event_type in cls._subscribers:
            cls._subscribers[event_type].remove(callback)
    
    @classmethod
    def emit(cls, event_type, data=None):
        Logger.debug(f"Event \"{event_type}\" emitted with data: \"{data}\"")

        for callback in cls._subscribers.get(event_type, []):
            try:
                callback(data)
            except Exception as e:
                Logger.exception(f"Event callback error: {e}")