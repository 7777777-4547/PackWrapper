from .Logger import Logger
from .Utils import Event, EventType

CONFIGURED = False

def change_configure_status(status: bool) -> None:
    
    Event.emit_withdata(EventType.CONFIGURED_CHANGE, status)
    
    global CONFIGURED
    CONFIGURED = status
    
    Event.emit_withdata(EventType.CONFIGURED_CHANGED, status)


def get_configure_status() -> bool:
    
    Event.emit(EventType.CONFIGURED_GET)
    
    return CONFIGURED

def check_configure_status() -> None:
    
    Event.emit(EventType.CONFIGURED_CHECK)
    
    if not get_configure_status():
        Logger.exception("PackWrapper is not configured. Please configure it before using it." 
                         + "(Use 'PackWrapper.init()' to configure.)")
