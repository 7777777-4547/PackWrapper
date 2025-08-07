from .Logger import Logger
from .Utils import Event

CONFIGURED = False

def change_configure_status(status: bool) -> None:
    
    Event.emit("configure_status.change_start", status)
    
    global CONFIGURED
    CONFIGURED = status
    
    Event.emit("configure_status.change_end", status)


def get_configure_status() -> bool:
    
    Event.emit("configure_status.get")
    
    return CONFIGURED

def check_configure_status() -> None:
    
    Event.emit("configure_status.check")
    
    if not get_configure_status():
        Logger.exception("PackWrapper is not configured. Please configure it before using it." + 
                       "(Use 'PackWrapper.config(properties_file_path)' to configure.)")
