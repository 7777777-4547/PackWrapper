from .StatusChecker import check_configure_status
from . import Dependency
from .PathEnum import PackWrapper



# TODO: Not done yet.
class RunClient:
    
    game_dir = PackWrapper.GAME
    
    def __init__(self, java_args: str = "-Xmx2048m", **kwargs) -> None:        
        check_configure_status()
        client_config = {}
        client_config["ingame_setting"] = kwargs
        client_config["dependency"] = Dependency.get_dependencies()
        client_config["java_args"] = java_args
        
        self.client_config = client_config
                
    def get_config(self) -> dict:
        return self.client_config
        
    def run(self) -> None:
        config = self.get_config()
