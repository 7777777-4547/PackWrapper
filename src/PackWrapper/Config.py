from pydantic import BaseModel, Field, ValidationError
from pathlib import Path
import json5
import json


class PackWrapper(BaseModel):
    debug_mode: bool = False


class PackInfo(BaseModel):
    name: str
    version: str
    source_dir: str
    package_name: str | None = None

    def model_post_init(self, __context):
        if self.package_name is None:
            self.package_name = self.name

    class Config:
        extra = "allow"


class PWConfig(BaseModel):
    packwrapper: PackWrapper = Field(default_factory=PackWrapper)
    pack_info: PackInfo

    class Config:
        extra = "allow"


class ConfigManager:
    PROPERTIES_SUFFIX = [".json", ".json5"]

    @classmethod
    def suffix_with(cls, file_path_without_suffix: str | Path) -> Path:

        file_path_without_suffix = Path(file_path_without_suffix)

        for suffix in ConfigManager.PROPERTIES_SUFFIX:
            file_path = file_path_without_suffix.with_name(
                file_path_without_suffix.name + suffix
            )

            if file_path.exists():
                return file_path

        else:
            raise Exception(
                f'Cannot find the properties file: "{file_path_without_suffix}"'
            )

    @classmethod
    def read_config(cls, file_path_without_suffix) -> dict:

        file_path = cls.suffix_with(file_path_without_suffix)

        file_suffix = Path(file_path).suffix

        match file_suffix:
            case ".json":
                return cls.json_load(file_path)
            case ".json5":
                return cls.json5_load(file_path)
            case _:
                raise Exception(f'Unknown properties file format: "{file_path}"')

    @classmethod
    def validate_config(cls, config: dict):

        try:
            PWConfig(**config)
        except ValidationError as e:
            raise Exception(json.dumps(e.errors(), indent=4))

    @classmethod
    def json_load(cls, file_path) -> dict:

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = json.load(file)

            return content

        except Exception:
            raise Exception(f'Cannot read the properties: "{file_path}"')

    @classmethod
    def json5_load(cls, file_path) -> dict:

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = json5.load(file)

            return dict(content)

        except Exception:
            raise Exception(f'Cannot read the properties: "{file_path}"')
