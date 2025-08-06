from .Logger import Logger
from .Utils import Event

CONFIGURED = False

def change_configure_status(status: bool) -> None:
    
    Event.emit(change_configure_status.__name__, status)
    
    global CONFIGURED
    CONFIGURED = status

def get_configure_status() -> bool:
    
    Event.emit(get_configure_status.__name__)
    
    return CONFIGURED

def check_configure_status() -> None:
    
    Event.emit(check_configure_status.__name__)
    
    if not get_configure_status():
        Logger.exception("PackWrapper is not configured. Please configure it before using it." + 
                       "(Use 'PackWrapper.config(properties_file_path)' to configure.)")
