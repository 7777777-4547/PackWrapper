from .logger import Logger
from .utils import PackWrapperPath, EntryPoint

from pathlib import Path
from typing import Callable, Literal, overload
from string import Template
from enum import StrEnum
from abc import ABC, abstractmethod
from PIL import Image
import zipfile
import asyncio
import shutil
import json


class ContentEntryPoint(StrEnum):
    INIT_PLUGINS = "init_plugins"
    EXPORT_CLEAN = "export_clean"
    EXPORT_COPY = "export_copy"
    PACKAGE = "package"


class Content(ABC):
    @abstractmethod
    def __init__(
        self,
        source_dir: Path,
        name: str,
        package_name: str | None = None,
        compresslevel: int = 5,
        **extra_properties,
    ):
        self.source_dir = Path(source_dir).absolute()
        self.name = name
        self.export_dir = (PackWrapperPath.EXPORT / self.source_dir.name).absolute()

        self.files: set[Path] = set(
            [item for item in self.source_dir.rglob("*") if item.is_file()]
        )
        self.custom_files: dict[Path, Path] = {}

        self.properties = {
            "name": name,
            **extra_properties,
        }

        self.package_name = (
            self.template_substitute(package_name, **self.properties)
            if package_name is not None
            else name
        )
        self.package_file = PackWrapperPath.PACKAGE / f"{self.package_name}.zip"
        self.compresslevel = compresslevel

        self.plugins = []
        self.plugins_namelist = []

    @abstractmethod
    def __enter__(self):
        return self

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def get_source_dir(self) -> Path:
        """
        Get the source directory.
        """
        return self.source_dir

    def get_export_dir(self) -> Path:
        """
        Get the export directory.
        """
        return self.export_dir

    def get_files(self) -> set[Path]:
        """
        Get all files in the source directory by default.
        Using `include_files`/`include_file` or `exclude_files`/`exclude_file` to modify the files.
        """
        return self.files

    def include_files(self, files: dict[Path, Path]):
        """
        Include files to the export directory.
        Args:
            files (dict[Path, Path]): key is the source file (relative to the source directory), value is the destination file (relative to the export directory).
        """
        self.custom_files.update(files)

    @overload
    def include_file(self, src_file: Path): ...
    @overload
    def include_file(self, src_file: Path, dst_file: Path): ...

    def include_file(self, src_file: Path, dst_file: Path | None = None):
        """
        Include file to the export directory.
        Args:
            file (Path): the source file (relative to the source directory).
            custom (Path): the destination file (relative to the export directory).
        """
        self.custom_files.update(
            {
                src_file: (
                    dst_file
                    if dst_file is not None
                    else self.export_dir / Path(src_file).name
                )
            }
        )

    def exclude_files(self, files: list[Path]):
        """
        Exclude files from the export directory (relative to the source/export directory).
        Args:
            files (list[Path]): the files to exclude.
        """
        files_ = set(files)
        self.files = self.files - files_
        self.custom_files = {
            src_file: dst_file
            for src_file, dst_file in self.custom_files.items()
            if src_file not in files_
        }

    def exclude_file(self, file: Path):
        """
        Exclude file from the export directory (relative to the source/export directory).
        Args:
            file (Path): the file to exclude.
        """
        self.files.remove(file)
        if file in self.custom_files:
            del self.custom_files[file]

    @staticmethod
    def relative_files(
        files: list[Path] | set[Path], base_dir: Path, rebase_dir: Path
    ) -> dict[Path, Path]:
        """
        Relative to files from the source directory to the export directory.
        Args:
            files (list[Path] | set[Path]): the files to rebase.
            base_dir (Path): the base directory.
            rebase_dir (Path): the rebase directory.
        Returns:
            dict[Path, Path]: key is the source file (relative to the source directory), value is the destination file (relative to the export directory).
        """

        def rebase_check(file: Path):
            try:
                rebase_file = rebase_dir / file.relative_to(base_dir)
            except ValueError:
                Logger.warning(
                    f'Cannot directly rebase the file: "{file}", backward to rebase on the rebase directory.'
                )
                rebase_file = rebase_dir / file.name
            return rebase_file

        return {file: rebase_check(file) for file in files}

    @staticmethod
    def relative_file(file: Path, base_dir: Path, rebase_dir: Path) -> Path:
        """
        Relative to file from the source directory to the export directory.
        Args:
            file (Path): the file to rebase.
            base_dir (Path): the base directory.
            rebase_dir (Path): the rebase directory.
        Returns:
            Path: the destination file (relative to the export directory).
        """
        return rebase_dir / file.relative_to(base_dir)

    @staticmethod
    def template_substitute(template: str, **kwargs):
        """
        Substitute the template with the given variables.
        """
        return Template(template).substitute(kwargs)

    @EntryPoint(
        "create",
        ContentEntryPoint.EXPORT_CLEAN,
    )
    def export_clean(self):
        if self.export_dir.exists():
            Logger.warning(
                f'The export directory "{self.export_dir}" is already exists, it will be deleted and recreated.',
                stack_info=False,
            )
            shutil.rmtree(self.export_dir)

    @EntryPoint(
        "create",
        ContentEntryPoint.EXPORT_COPY,
    )
    def export_copy(self):
        self.dest_files: set[Path] = set()
        for file, dest_file in {
            **self.relative_files(self.files, self.source_dir, self.export_dir),
            **self.custom_files,
        }.items():
            try:
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file, dest_file)
            except Exception as e:
                Logger.exception(
                    f'Cannot copy the file: "{file}" to "{dest_file}"', exc_info=e
                )

    @EntryPoint(
        "create",
        ContentEntryPoint.PACKAGE,
    )
    def package(self):
        try:
            with zipfile.ZipFile(
                self.package_file,
                "w",
                zipfile.ZIP_DEFLATED,
                compresslevel=self.compresslevel,
            ) as zipf:
                for file in (self.export_dir).rglob("*"):
                    if file.is_file():
                        relative_file = file.relative_to(self.export_dir)
                        zipf.write(file, relative_file)

        except Exception:
            Logger.debug(f"{self.package_file}")
            Logger.exception(f'Cannot packaging the pack: "{self.package_name}"')

    @abstractmethod
    def build(self):
        """
        Build the content.
        """
        self.init_plugins()
        self.export_clean()
        self.export_copy()
        self.package()

    @EntryPoint(
        "create",
        ContentEntryPoint.INIT_PLUGINS,
    )
    def init_plugins(self):
        """
        Initialize the plugins.
        """
        Logger.info(f"Plugins registered: {self.plugins_namelist}")
        for plugin in self.plugins:
            plugin()

    def register_plugin(self, plugin: Callable):
        """
        Register a plugin.
        Args:
            plugin (Callable): the plugin to register.
        """
        if callable(plugin):
            self.plugins.append(plugin)
            self.plugins_namelist.append(type(plugin).__name__)

    def register_plugins(self, *plugin: Callable):
        """
        Register plugins.
        Args:
            plugins (list[Callable]): the plugins to register.
        """
        for plugin_ in plugin:
            self.register_plugin(plugin_)


class ResourcepackEntryPoint(StrEnum):
    EXPORT_DUMP_MCMETA = "export_dump_mcmeta"


class Resourcepack(Content):
    def __init__(
        self,
        source_dir: Path,
        name: str,
        description: str,
        verfmt: int
        | tuple[int, int]
        | list[int]
        | float
        | tuple[float, float]
        | list[float],
        icon: Path | None = None,
        license: Path | None = None,
        extra_mcmeta: dict | None = None,
        package_name: str | None = None,
        compresslevel: int = 5,
        **extra_properties,
    ):
        super().__init__(
            source_dir,
            name,
            package_name,
            compresslevel,
            **extra_properties,
        )
        self.description = self.template_substitute(description, **self.properties)
        self.verfmt = verfmt
        self.icon = icon
        self.license = license
        self.pack_mcmeta = {"pack": {"description": self.description}}

        if extra_mcmeta is not None:
            self.pack_mcmeta.update(extra_mcmeta)
        if self.icon is not None:
            self.include_file(self.icon, self.export_dir / "pack.png")
        if self.license is not None:
            self.include_file(self.license)

        if not isinstance(verfmt, (int, float)) and len(verfmt) > 2:
            Logger.exception(f"The max verfmt len is 2, but got {len(verfmt)}!")
        if not isinstance(verfmt, (int, float)) and verfmt[0] > verfmt[-1]:
            Logger.exception(f"The verfmt is invalid: {verfmt}")

        def verfmt_spliter(num: int | float):
            parts = str(num).split(".")
            parts = tuple(int(part) for part in parts)
            return parts if len(parts) != 1 else (parts[0], 0)

        def verfmt_standardizer(
            verfmt_min: int | float,
            verfmt_max: int | float,
            mode: Literal["legacy", "compatible", "default"],
        ) -> dict:
            match mode:
                case "legacy":
                    verfmt_min, verfmt_max = map(int, [verfmt_min, verfmt_max])
                    return (
                        {"pack_format": verfmt_min}
                        if (verfmt_min == verfmt_max)
                        else {
                            "pack_format": verfmt_min,
                            "supported_formats": [verfmt_min, verfmt_max],
                        }
                    )
                case "compatible":
                    return {
                        "pack_format": int(verfmt_min),
                        "supported_formats": [int(verfmt_min), int(verfmt_max)],
                        "min_format": verfmt_spliter(verfmt_min),
                        "max_format": verfmt_spliter(verfmt_max),
                    }
                case "default":
                    return {
                        "min_format": verfmt_spliter(verfmt_min),
                        "max_format": verfmt_spliter(verfmt_max),
                    }
                case _:
                    Logger.exception(
                        f'The mode "{mode}" is not supported!', exc_info=ValueError
                    )

        self.verfmt_min = verfmt if isinstance(verfmt, (int, float)) else verfmt[0]
        self.verfmt_max = verfmt if isinstance(verfmt, (int, float)) else verfmt[-1]

        if (self.verfmt_min < 65) and (self.verfmt_max < 65):
            self.verfmt_min = int(self.verfmt_min)
            self.verfmt_max = int(self.verfmt_max)
            self.pack_mcmeta.get("pack", {}).update(
                verfmt_standardizer(self.verfmt_min, self.verfmt_max, "legacy")
            )
        elif (self.verfmt_min < 65) and (self.verfmt_max >= 65):
            if self.verfmt_min < 15:
                Logger.warning(
                    "The pack's minimum format is too low, it may not be compatible with"
                    " the version 1.21.9 or higher of Minecraft. Now it changed to 15.",
                    stack_info=False,
                )
                self.verfmt_min = 15
            self.pack_mcmeta.get("pack", {}).update(
                verfmt_standardizer(self.verfmt_min, self.verfmt_max, "compatible")
            )
        else:
            self.pack_mcmeta.get("pack", {}).update(
                verfmt_standardizer(self.verfmt_min, self.verfmt_max, "default")
            )

    def __enter__(self):
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return super().__exit__(exc_type, exc_val, exc_tb)

    @EntryPoint("create", ResourcepackEntryPoint.EXPORT_DUMP_MCMETA)
    def export_dump_mcmeta(self):
        try:
            with open(self.export_dir / "pack.mcmeta", "w", encoding="utf-8") as f:
                json.dump(self.pack_mcmeta, f, ensure_ascii=False, indent=4)
        except Exception:
            Logger.exception(
                f'Cannot dump the resourcepack mcmeta: "{self.export_dir / "pack.mcmeta"}"'
            )


    def build(self):
        """
        Run the resourcepack.
        """
        self.init_plugins()
        Logger.info(f'Starting export: "{self.package_name}"')
        self.export_clean()
        self.export_copy()
        self.export_dump_mcmeta()
        Logger.info(f'Finished exporting: "{self.export_dir}"')
        Logger.info("Packaging...")
        Logger.debug(f'The package path: "{self.package_file}"')
        self.package()
        Logger.info(f'Finished packaging: "{self.package_file}"')

    @staticmethod
    def get_as_images_async(files: list[Path]):

        async def _get_as_image(file: Path):
            image = await asyncio.to_thread(Image.open, file)
            return image

        result = asyncio.gather(*[_get_as_image(file) for file in files])
        return result
