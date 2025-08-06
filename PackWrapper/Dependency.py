from typing import Literal, TypeAlias, Union
from pathlib import Path

# TODO: Maven Support, Version

ContentType: TypeAlias = Literal["mod", "resourcepack", "datapack"]

DependencyType: TypeAlias = Literal["required", "optional", "incompatible"]
Connections: TypeAlias = Union[DependencyType, Literal["runtime_only"]]


class Dependency:

    _dependencies: dict[Connections, dict[ContentType, str | Path]]

    @classmethod    
    def _new(cls, file_path: str | Path, content_type: ContentType, connection: Connections):
        cls._dependencies.update({connection: {content_type: file_path}})
        
        
    @classmethod       
    def required(cls, file_path: str | Path, content_type: ContentType):
        cls._new(file_path, content_type, "required")
        
    @classmethod
    def optional(cls, file_path: str | Path, content_type: ContentType):
        cls._new(file_path, content_type, "optional")
        
    @classmethod
    def incompatible(cls, file_path: str | Path, content_type: ContentType):
        cls._new(file_path, content_type, "incompatible")
        
    @classmethod       
    def runtime_only(cls, file_path: str | Path, content_type: ContentType):
        cls._new(file_path, content_type, "runtime_only")
    
    @classmethod     
    def get_dependencies(cls):
        return cls._dependencies


__all__ = [
    "ContentType",
    "DependencyType",
    "Connections",
    
    "Dependency"
]