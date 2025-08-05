from .PathEnum import PackWrapper
from .Logger import Logger
from .StatusChecker import check_configure_status

from typing import Literal, TypeAlias
from string import Template
from pathlib import Path
import shutil
import json
import zipfile

class Resourcepack():

    '''
    Resourcepack exporting class, 
    if you want to use it you can use the `PackWrapper.config()` function, 
    and must provide the right properties contect to use it.    
    '''
    
    compresslevels: TypeAlias = Literal[0,1,2,3,4,5,6,7,8,9]
    
    def __init__(self, 
                 source_dir: str | Path,
                 name: str,
                 description: str, 
                 verfmt: int | tuple[int,int] | list[int], 
                 icon_path: str | Path | None = None,
                 **extra_properties
                 ):
        
        check_configure_status()
        
        self.name = name
        self.verfmt = verfmt if isinstance(verfmt, (int, list)) else list(verfmt)
        self.icon_path = Path(icon_path) if icon_path is not None else None
        self.source_dir = Path(source_dir)
        
        self.properties = {
            "name": name,
            "description": description,
            "verfmt": verfmt,
            "source_dir": str(source_dir),
            **extra_properties
        }
        
        self.description = Template(description).substitute(self.properties)
        
        self.properties["description"] = self.description
        
        self.pack_mcmeta = {
            "pack":{
                "pack_format": verfmt,
                "description": self.description
            }
        } if isinstance(verfmt, int) else {
            "pack":{
                "pack_format": verfmt[0],
                "supported_formats": verfmt,
                "description": self.description
            }
        }
    
    
    def export(self, compresslevel: compresslevels = 5, export_name: str | None = None):
        
        '''
        The function to export the resourcepack, compresslevel is the level of compression, 1-9, 5 is the default.
        `export_name` is optional, if not specified, the name of the resourcepack will be used.
        '''
        properties = self.properties
        
        if export_name is None:
            export_name = self.name
        else:
            try:
                export_name = Template(export_name).substitute(properties)
            except Exception:
                Logger.error(f"Invalid export_name template \"{export_name}\", return to the original string.")
                export_name = export_name
        
        Logger.info(f"Starting export: \"{export_name}\"")
        
        cache_dir = PackWrapper.CACHE / self.source_dir.name
        cache_dir.mkdir(parents=True, exist_ok=True)
        Logger.debug(f"The resourcepack cache directory: \"{cache_dir}\"")
        export_path = PackWrapper.EXPORT / f"{export_name}.zip"
        Logger.debug(f"The export final destination path: \"{export_path}\"")
        
        
        # Copy files
        Logger.info("Copying files...")
        try:
            for file in self.source_dir.rglob("*"):
                if file.is_file():
                    
                    rel_path = file.relative_to(self.source_dir)
                    dest_path = cache_dir / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    try: shutil.copy2(file, dest_path)
                    except Exception: Logger.exception(f"Cannot copy the file: \"{file}\" to \"{dest_path}\"")
                    
        except Exception:
            Logger.exception(f"Cannot copy the files: {self.source_dir}")
        
        if self.icon_path is not None:
            try: shutil.copy2(self.icon_path, cache_dir / "pack.png")
            except Exception: Logger.warning(f"Cannot copy the icon: \"{self.icon_path}\" to \"{cache_dir / self.icon_path.name}\"")

        
        # Dump resourcepack mcmeta
        Logger.info("Dumping resourcepack mcmeta...")
        try:
            with open(cache_dir / "pack.mcmeta", 'w', encoding='utf-8') as f:
                json.dump(self.pack_mcmeta, f, ensure_ascii=False, indent=4)
            
        except Exception:
            Logger.exception(f"Cannot dump the resourcepack mcmeta: \"{cache_dir / "pack.mcmeta"}\"")
            
        
        # Packing
        Logger.info("Packing and exporting...")
        Logger.debug(f"The export path: \"{export_path}\"")
        try:
            with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED, compresslevel = compresslevel) as zipf:
                for file in (cache_dir).rglob('*'):
                    if file.is_file():
                        relative_path = file.relative_to(cache_dir)
                        zipf.write(file, relative_path)
            
        except Exception:
            Logger.exception(f"Cannot export the pack: \"{export_name}\"")
            
                    
        # Clean up            
        Logger.info("Cleaning up...")
        try: shutil.rmtree(str(PackWrapper.CACHE))
        except Exception: Logger.exception(f"Cannot remove the cache folder: \"{PackWrapper.CACHE}\"")
        
        
        Logger.info(f"Finished exporting: \"{export_path}\"")


class ResourcepackAuto():
    
    '''
    Simply automatic resourcepack exporting class, 
    if you want to use it you need to use the `PackWrapper.config()` function firstly, 
    and must provide the right properties contect(not the file path) to use it.
    
    The properties must provide these keys: `name`, `verfmt`, `description`, `source_dir`.
    `icon_path` and `export_name` are optional.
    '''
    
    compresslevels: TypeAlias = Literal[0,1,2,3,4,5,6,7,8,9]
    
    def __init__(self, properties: dict):
        
        check_configure_status()
        
        self.properties = properties
        try:
            self.name = properties["name"]
            self.description = properties["description"]
            self.verfmt = properties["verfmt"]
            self.source_dir = properties["source_dir"]
        except Exception: Logger.exception("Cannot read the properties")
        
        try:
            self.icon_path = properties["icon_path"]
        except Exception: 
            self.icon_path = None
            
        try:
            self.export_name = properties["export_name"]
            main_properties = {"name", "description", "verfmt", "source_dir", "export_name", "icon_path"}
        except KeyError:
            self.export_name = None
            main_properties = {"name", "description", "verfmt", "source_dir", "icon_path"}
        
        self.extra_properties = {k: v for k, v in properties.items() if k not in main_properties}
        
                    
        if not isinstance(self.verfmt, (int, list)):
            self.verfmt = list(self.verfmt)
        
        self.pack_mcmeta = {
            "pack":{
                "pack_format": self.verfmt,
                "description": self.description
            }
        } if isinstance(self.verfmt, int) else {
            "pack":{
                "pack_format": self.verfmt[0],
                "supported_formats": self.verfmt,
                "description": self.description
            }
        }
    
    def export(self, compresslevel: compresslevels = 5):
        
        export_name = self.export_name
        
        '''
        The function to export the resourcepack, compresslevel is the level of compression, 1-9, 5 is the default.
        `export_name` is optional, if not specified, the name of the resourcepack will be used.
        '''
        
        Resourcepack(
            self.source_dir, self.name, self.description, self.verfmt, self.icon_path, **self.extra_properties
        ).export(compresslevel, export_name = export_name)