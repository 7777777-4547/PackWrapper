CONFIGURED = False

def change_configure_status(status: bool) -> None:

    global CONFIGURED
    CONFIGURED = status


def get_configure_status() -> bool:

    return CONFIGURED