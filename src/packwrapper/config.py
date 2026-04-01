from enum import StrEnum
from pydantic import BaseModel, Field, ValidationError
from pathlib import Path
import logging
import json5
import toml
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
    class PROPERTIES_SUFFIX(StrEnum):
        JSON = ".json"
        JSON5 = ".json5"
        TOML = ".toml"

    @classmethod
    def suffix_with(cls, file_path_without_suffix: str | Path) -> Path:

        if not isinstance(file_path_without_suffix, str | Path):
            raise TypeError(
                f"Expected str or Path, got {type(file_path_without_suffix).__name__}"
            )

        file_path_without_suffix = Path(file_path_without_suffix)

        for suffix in ConfigManager.PROPERTIES_SUFFIX:
            file_path = file_path_without_suffix.with_name(
                file_path_without_suffix.name + suffix
            )

            if file_path.exists():
                return file_path

        else:
            available_files = []
            for suffix in ConfigManager.PROPERTIES_SUFFIX:
                candidate = file_path_without_suffix.with_name(
                    file_path_without_suffix.name + suffix
                )
                available_files.append(str(candidate))

            raise FileNotFoundError(
                f'Cannot find the properties file: "{file_path_without_suffix}". '
                f"Expected one of: {', '.join(available_files)}"
            )

    @classmethod
    def read_config(cls, file_path_without_suffix: str | Path) -> dict:

        try:
            file_path = cls.suffix_with(file_path_without_suffix)
        except FileNotFoundError as e:
            logging.error(str(e))
            raise
        except TypeError as e:
            error_msg = f'Invalid path type: {str(e)}'
            logging.error(error_msg)
            raise TypeError(error_msg) from e

        file_suffix = Path(file_path).suffix

        match file_suffix:
            case cls.PROPERTIES_SUFFIX.JSON:
                return cls.json_load(file_path)
            case cls.PROPERTIES_SUFFIX.JSON5:
                return cls.json5_load(file_path)
            case cls.PROPERTIES_SUFFIX.TOML:
                return cls.toml_load(file_path)
            case _:
                raise Exception(f'Unknown properties file format: "{file_path}"')

    @classmethod
    def dump_config(cls, config: dict):
        try:
            raw_output = toml.dumps(config)
            split_output = raw_output.split("\n")
            for line in split_output:
                if len(line) == 0:
                    continue
                yield line

        except TypeError as e:
            error_msg = f'Cannot serialize config to TOML: contains unsupported data types. Details: {str(e)}'
            logging.error(error_msg)
            raise TypeError(error_msg) from e

        except Exception as e:
            error_msg = f'Unexpected error while dumping config: {type(e).__name__}: {str(e)}'
            logging.exception(error_msg)
            raise RuntimeError(error_msg) from e

    @classmethod
    def validate_config(cls, config: dict):

        try:
            PWConfig(**config)

        except ValidationError as e:
            error_details = json.dumps(e.errors(), indent=4, ensure_ascii=False)
            error_msg = f'Configuration validation failed:\n{error_details}'
            logging.error(error_msg)
            raise ValueError(error_msg) from e

    @classmethod
    def json_load(cls, file_path: str | Path) -> dict:

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = json.load(file)

            return content

        except FileNotFoundError:
            error_msg = f'Properties file not found: "{file_path}"'
            logging.error(error_msg)
            raise FileNotFoundError(error_msg) from None

        except PermissionError:
            error_msg = f'Permission denied to read properties file: "{file_path}"'
            logging.error(error_msg)
            raise PermissionError(error_msg) from None

        except json.JSONDecodeError as e:
            error_msg = f'Invalid JSON format in "{file_path}": {e.msg}'
            logging.error(error_msg)
            raise ValueError(error_msg) from e

        except UnicodeDecodeError:
            error_msg = (
                f'Encoding error reading "{file_path}": file must be UTF-8 encoded'
            )
            logging.error(error_msg)
            raise ValueError(error_msg) from None

        except Exception as e:
            error_msg = f'Unexpected error reading properties file "{file_path}": {type(e).__name__}: {str(e)}'
            logging.exception(error_msg)
            raise RuntimeError(error_msg) from e

    @classmethod
    def json5_load(cls, file_path: str | Path) -> dict:

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = json5.load(file)

            return dict(content)

        except FileNotFoundError:
            error_msg = f'Properties file not found: "{file_path}"'
            logging.error(error_msg)
            raise FileNotFoundError(error_msg) from None

        except PermissionError:
            error_msg = f'Permission denied to read properties file: "{file_path}"'
            logging.error(error_msg)
            raise PermissionError(error_msg) from None

        except Exception as e:
            if "JSONDecodeError" in type(e).__name__:
                error_msg = f'Invalid JSON5 format in "{file_path}": {str(e)}'
                logging.error(error_msg)
                raise ValueError(error_msg) from e
            else:
                error_msg = f'Unexpected error reading properties file "{file_path}": {type(e).__name__}: {str(e)}'
                logging.exception(error_msg)
                raise RuntimeError(error_msg) from e

    @classmethod
    def toml_load(cls, file_path: str | Path) -> dict:

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = toml.load(file)

            return content

        except FileNotFoundError:
            error_msg = f'Properties file not found: "{file_path}"'
            logging.error(error_msg)
            raise FileNotFoundError(error_msg) from None

        except PermissionError:
            error_msg = f'Permission denied to read properties file: "{file_path}"'
            logging.error(error_msg)
            raise PermissionError(error_msg) from None

        except toml.TomlDecodeError as e:
            error_msg = f'Invalid TOML format in "{file_path}": {str(e)}'
            logging.error(error_msg)
            raise ValueError(error_msg) from e

        except UnicodeDecodeError:
            error_msg = (
                f'Encoding error reading "{file_path}": file must be UTF-8 encoded'
            )
            logging.error(error_msg)
            raise ValueError(error_msg) from None

        except Exception as e:
            error_msg = f'Unexpected error reading properties file "{file_path}": {type(e).__name__}: {str(e)}'
            logging.exception(error_msg)
            raise RuntimeError(error_msg) from e
