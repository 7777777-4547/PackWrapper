from .PathEnum import PackWrapper
from .Logger import Logger
from .Utils import Event
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
                 verfmt: int | tuple[int,int] | list[int]  |  float | tuple[float,float] | list[float], 
                 icon_path: str | Path | None = None,
                 **extra_properties
                 ):
        
                
        def _verfmt_correctness_check(verfmt: int | tuple[int,int] | list[int]  |  float | tuple[float,float] | list[float]):
            
            if (not isinstance(verfmt, (int,float))) and len(verfmt) > 2:
                Logger.exception(f"The max verfmt len is 2, but got {len(verfmt)}!")
                raise
            
            if not isinstance(verfmt, (int,float)) and verfmt[0] > verfmt[-1]:
                Logger.exception(f"The verfmt is invalid: {verfmt}")

        
        def _decimal_convert(num: int | float):
            parts = str(num).split('.')
            parts = tuple(int(part) for part in parts)
            
            if len(parts) == 1:
                return (parts[0], 0)
            else:
                return parts
        
        
        check_configure_status()
        
        Event.emit("resourcepack.create_start")
        
        _verfmt_correctness_check(verfmt)
        
        self.name = name
        self.verfmt = verfmt if isinstance(verfmt, (int,float,list)) else list(verfmt)
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
        
        self.verfmt_min = verfmt_min = verfmt if isinstance(verfmt, (int,float)) else verfmt[0]
        self.verfmt_max = verfmt_max = verfmt if isinstance(verfmt, (int,float)) else verfmt[-1]

        if (verfmt_min < 65) and (verfmt_max < 65):
            
            verfmt_min = int(verfmt_min)
            verfmt_max = int(verfmt_max)
            
            self.pack_mcmeta = {
                "pack":{
                    "pack_format": verfmt,
                    "description": self.description
                }
            } if isinstance(verfmt, int) else {
                "pack":{
                    "pack_format": verfmt_min,
                    "supported_formats": [verfmt_min, verfmt_max],
                    "description": self.description
                }
            }
        elif (verfmt_min < 65) and (verfmt_max >= 65):
            
            if verfmt_min < 15:
                Logger.warning("The pack's minimum format is too low, it may not be compatible with " + 
                               "the version 1.21.9 or higher of Minecraft. Now it changed to 15.")
                verfmt_min = 15
            
            self.pack_mcmeta = {
                "pack":{
                    "pack_format": int(verfmt_min),
                    "description": self.description,
                    "supported_formats": [int(verfmt_min), int(verfmt_max)],
                    "min_format": _decimal_convert(verfmt_min),
                    "max_format": _decimal_convert(verfmt_max)
                }
            }
        else:
            self.pack_mcmeta = {
                "pack":{
                    "min_format": _decimal_convert(verfmt_min),
                    "max_format": _decimal_convert(verfmt_max),
                    "description": self.description,                    
                }
            }
            
        self.cache_dir = PackWrapper.EXPORT / self.source_dir.name
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        Logger.debug(f"The resourcepack cache directory: \"{self.cache_dir}\"")
    
        Event.emit("resourcepack.create_end")
    
    
    def export(self, export_name: str | None = None):
        
        '''
        The function to export the resourcepack, compresslevel is the level of compression, 1-9, 5 is the default.
        `export_name` is optional, if not specified, the name of the resourcepack will be used.
        '''
        cache_dir = self.cache_dir
        properties = self.properties
        
        if export_name is None:
            export_name = self.name
        else:
            try:
                export_name = Template(export_name).substitute(properties)
            except Exception:
                Logger.error(f"Invalid export_name template \"{export_name}\", return to the original string.")
                export_name = export_name
                
        self.export_name = export_name
        
        Logger.info(f"Starting export: \"{export_name}\"")
        Event.emit("resourcepack.export_start")
                        
        # Copy files
        Logger.info("Copying files...")
        Event.emit("resourcepack.export_copy_start")
        
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

        Event.emit("resourcepack.export_copy_end")
        
        
        # Dump resourcepack mcmeta
        Logger.info("Dumping resourcepack mcmeta...")
        Event.emit("resourcepack.export_dump_start")
        
        try:
            with open(cache_dir / "pack.mcmeta", 'w', encoding='utf-8') as f:
                json.dump(self.pack_mcmeta, f, ensure_ascii=False, indent=4)
            
        except Exception:
            Logger.exception(f"Cannot dump the resourcepack mcmeta: \"{cache_dir / "pack.mcmeta"}\"")
            
        Event.emit("resourcepack.export_dump_end")
        Logger.info(f"Finished exporting: \"{cache_dir}\"")
        Event.emit("resourcepack.export_end")


    def package(self, compresslevel: compresslevels = 5):
        
        cache_dir = self.cache_dir        
        export_name = self.export_name
        export_path = PackWrapper.PACKAGE / f"{export_name}.zip"
        Logger.debug(f"The package destination path: \"{export_path}\"")
        
        # Packing
        Logger.info("Packing...")
        Logger.debug(f"The package path: \"{export_path}\"")
        Event.emit("resourcepack.package_start")
        
        try:
            with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED, compresslevel = compresslevel) as zipf:
                for file in (cache_dir).rglob('*'):
                    if file.is_file():
                        relative_path = file.relative_to(cache_dir)
                        zipf.write(file, relative_path)
            
        except Exception:
            Logger.exception(f"Cannot packaging the pack: \"{export_name}\"")
                
        Logger.info(f"Finished packaging: \"{export_path}\"")

        Event.emit("resourcepack.package_end")