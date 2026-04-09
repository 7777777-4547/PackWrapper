from .config import ConfigManager
from .logger import Logger
from .plugin import Plugin
from .utils import PackWrapperPath, EntryPoint

from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from pathlib import Path
from typing import Any, Iterator, Literal, overload
from string import Template
from enum import StrEnum
from abc import ABC, abstractmethod
from PIL import Image
from io import BytesIO
import zipfile
import shutil
import json


class ContentEntryPoint(StrEnum):
    INIT_PLUGINS = "init_plugins"
    EXPORT_CLEAN = "export_clean"
    EXPORT_COPY = "export_copy"
    PACKAGE = "package"


class Content(ABC):
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

        self.plugins: dict[str, Plugin] = {}

    @abstractmethod
    def __enter__(self):
        return self

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            Logger.error(f"Error occurred during content processing: {exc_val}")
        return False

    def get_source_dir(self) -> Path:
        """
        Get the content's source directory.
        """
        return self.source_dir

    def get_export_dir(self) -> Path:
        """
        Get the content's export directory.
        """
        return self.export_dir

    def get_files(self, include_custom=False) -> set[Path]:
        """
        Get all files in the content's source directory by default.
        Using `include_files`/`include_file` or `exclude_files`/`exclude_file` to modify the files.
        Args:
            include_custom (bool): whether to include custom files (included by `include_file`/`include_files`).
        """
        return (
            {*self.files, *self.custom_files.keys()}
            if include_custom
            else self.files.copy()
        )

    def include_files(self, files: dict[Path, Path]):
        """
        Include files to the content's export directory.
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
        Include file to the content's export directory.
        Args:
            file (Path): the source file (relative to the content's source directory).
            custom (Path): the destination file (relative to the content's export directory).
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

    def exclude_files(self, files: list[Path] | set[Path]):
        """
        Exclude files from the content's export directory (relative to the content's source/export directory).
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
        Exclude file from the content's export directory (relative to the content's source/export directory).
        Args:
            file (Path): the file to exclude.
        """
        self.files.discard(file)
        if file in self.custom_files:
            del self.custom_files[file]

    @staticmethod
    def relative_files(
        files: list[Path] | set[Path], base_dir: Path, rebase_dir: Path
    ) -> dict[Path, Path]:
        """
        Relative to files from the base directory(`base_dir`) to the rebase directory(`rebase_dir`).
        Args:
            files (list[Path] | set[Path]): the files to rebase.
            base_dir (Path): the base directory.
            rebase_dir (Path): the rebase directory.
        Returns:
            dict[Path, Path]: key is the source file (relative to the base directory(`base_dir`)), value is the destination file (relative to the rebase directory(`rebase_dir`).
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
        Relative to file from the base directory(`base_dir`) to the rebase directory(`rebase_dir`).
        Args:
            file (Path): the file to rebase.
            base_dir (Path): the base directory.
            rebase_dir (Path): the rebase directory.
        Returns:
            Path: the destination file (relative to the rebase directory).
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
        """
        Clean the content's export directory.
        """
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
        """
        Copy the content's files to the export directory.
        """

        def _copy2(file, dest_file):
            try:
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file, dest_file)
            except Exception as e:
                Logger.exception(
                    f'Cannot copy the file: "{file}" to "{dest_file}"', exc_info=e
                )

        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(_copy2, file, dest_file)
                for file, dest_file in {
                    **self.relative_files(self.files, self.source_dir, self.export_dir),
                    **self.custom_files,
                }.items()
            ]
            for future in as_completed(futures):
                future.result()

    @EntryPoint(
        "create",
        ContentEntryPoint.PACKAGE,
    )
    def package(self):
        """
        Package the content.
        """
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

    @EntryPoint(
        "create",
        ContentEntryPoint.INIT_PLUGINS,
    )
    def init_plugins(self):
        """
        Initialize the content's plugins.
        """
        if self.plugins:
            Logger.info(f"Plugins registered: {list(self.plugins.keys())}")
            for plugin in self.plugins.values():
                plugin()
        else:
            Logger.info("No plugins registered, skipping")

    def register_plugin(self, plugin: Plugin):
        """
        Register a plugin.
        Args:
            plugin (Plugin): the plugin to register.
        """
        if callable(plugin):
            self.plugins[plugin.name] = plugin

    def register_plugins(self, *plugin: Plugin):
        """
        Register plugins.
        Args:
            plugins (list[Callable]): the plugins to register.
        """
        for plugin_ in plugin:
            self.register_plugin(plugin_)

    @abstractmethod
    def build(self):
        """
        Build the content.
        """
        self.init_plugins()
        self.export_clean()
        self.export_copy()
        self.package()


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
        optimization: bool = True,
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
        self.optimization = optimization

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

        self.verfmt_min = verfmt if isinstance(verfmt, (int, float)) else verfmt[0]
        self.verfmt_max = verfmt if isinstance(verfmt, (int, float)) else verfmt[-1]

        if (self.verfmt_min < 65) and (self.verfmt_max < 65):
            self.verfmt_min = int(self.verfmt_min)
            self.verfmt_max = int(self.verfmt_max)
            self.pack_mcmeta.get("pack", {}).update(
                self.verfmt_standardizer(self.verfmt_min, self.verfmt_max, "legacy")
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
                self.verfmt_standardizer(self.verfmt_min, self.verfmt_max, "compatible")
            )
        else:
            self.pack_mcmeta.get("pack", {}).update(
                self.verfmt_standardizer(self.verfmt_min, self.verfmt_max, "default")
            )

    @staticmethod
    def verfmt_spliter(num: int | float):
        parts = str(num).split(".")
        parts = tuple(int(part) for part in parts)
        return parts if len(parts) != 1 else (parts[0], 0)

    @staticmethod
    def verfmt_standardizer(
        verfmt_min: int | float,
        verfmt_max: int | float,
        mode: Literal["legacy", "compatible", "default"],
    ) -> dict:

        verfmt_spliter = Resourcepack.verfmt_spliter

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

    def _image_optimize(self, image: Image.Image):
        _buffer = BytesIO()
        try:
            image_dpi = image.info.get("dpi", (72, 72))
            image_colors_len = len(Counter(image.get_flattened_data()))

            if image_colors_len <= 256:
                image = image.convert(
                    "P",
                    palette=Image.Palette.ADAPTIVE,
                    colors=image_colors_len,
                )
            image.save(_buffer, "PNG", dpi=image_dpi, optimize=True)

            return _buffer.getvalue()

        finally:
            if image is not None:
                image.close()
            _buffer.close()

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

    @EntryPoint(
        "create",
        ContentEntryPoint.PACKAGE,
    )
    def package(self):
        """
        Package the content.
        """
        try:
            with zipfile.ZipFile(
                self.package_file,
                "w",
                zipfile.ZIP_DEFLATED,
                compresslevel=self.compresslevel,
            ) as zipf:
                for file in (self.export_dir).rglob("*"):

                    if not file.is_file():
                        continue

                    relative_file = file.relative_to(self.export_dir)

                    if file.suffix.lower() != ".png" or not self.optimization:
                        zipf.write(file, relative_file)
                    else:
                        image = Image.open(file).convert("RGBA")
                        zipf.writestr(
                            relative_file.as_posix(), self._image_optimize(image)
                        )

        except Exception:
            Logger.debug(f"{self.package_file}")
            Logger.exception(f'Cannot packaging the pack: "{self.package_name}"')

    def build(self):
        """
        Run the resourcepack.
        """
        Logger.info(f'Starting the build of the resourcepack: "{self.package_name}"')
        self.init_plugins()
        Logger.info("Exporting...")
        self.export_clean()
        self.export_copy()
        self.export_dump_mcmeta()
        Logger.info(f'Exported: "{self.export_dir}"')
        Logger.info("Packaging...")
        Logger.debug(f'The package path: "{self.package_file}"')
        if self.optimization:
            Logger.info("Optimization is enabled.")
        self.package()
        Logger.info(f'Packaged: "{self.package_file}"')

    def get_tex_files(self) -> Iterator[Path]:
        files = list(self.files)
        for file in files:
            if file.suffix.lower() != ".png":
                continue
            yield file.absolute()

    def get_tex_files_mapping(self) -> Iterator[tuple[Path, dict[str, Any]]]:
        for file in self.get_tex_files():
            _file_mcmeta = (file.parent / f"{file.name}.mcmeta").absolute()
            file_mcmeta = _file_mcmeta if _file_mcmeta in self.files else None
            mcmeta = ConfigManager.json_load(file_mcmeta) if file_mcmeta else {}
            yield file, {"mcmeta": file_mcmeta, "animated": "animation" in mcmeta}

    @overload
    def get_textures(self) -> list[Image.Image]: ...

    @overload
    def get_textures(self, files: list[Path] | None = None) -> list[Image.Image]: ...

    def get_textures(self, files: list[Path] | None = None):
        def _load_image(file: Path):
            return Image.open(file).copy()

        with ThreadPoolExecutor() as executor:
            return list(executor.map(_load_image, files or list(self.get_tex_files())))
