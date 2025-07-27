from typing import Literal, TypeAlias, Union
from pathlib import Path

# TODO: Maven Support, Version

ContentType: TypeAlias = Literal["mod", "resourcepack", "datapack"]

DependencyType: TypeAlias = Literal["required", "optional", "incompatible"]
Connections: TypeAlias = Union[DependencyType, Literal["runtime_only"]]

_dependencies: dict[Connections, dict[ContentType, str | Path]]

    
def _new(file_path: str | Path, content_type: ContentType, connection: Connections):
    global _dependencies
    _dependencies.update({connection: {content_type: file_path}})
    
    
def required(file_path: str | Path, content_type: ContentType):
    _new(file_path, content_type, "required")

def optional(file_path: str | Path, content_type: ContentType):
    _new(file_path, content_type, "optional")

def incompatible(file_path: str | Path, content_type: ContentType):
    _new(file_path, content_type, "incompatible")
    
def runtime_only(file_path: str | Path, content_type: ContentType):
    _new(file_path, content_type, "runtime_only")
    
def get_dependencies():
    return _dependencies


__all__ = [
    "ContentType",
    "DependencyType",
    "Connections",
    
    "required",
    "optional",
    "incompatible",
    "runtime_only",
    "get_dependencies"
]