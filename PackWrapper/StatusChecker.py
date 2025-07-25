from .Logger import Logger

CONFIGURED = False

def change_configure_status(status: bool) -> None:
    global CONFIGURED
    CONFIGURED = status

def get_configure_status() -> bool:
    return CONFIGURED

def check_configure_status() -> None:
    if not get_configure_status():
        Logger.exception("PackWrapper is not configured. Please configure it before using it." + 
                       "(Use 'PackWrapper.config(properties_file_path)' to configure.)")
