from packwrapper.content import ContentEntryPoint
from packwrapper.config import ConfigManager
from packwrapper.logger import Logger
from packwrapper.plugin import Plugin, plugin_logger
from packwrapper.utils import EntryPoint
from packwrapper import Resourcepack

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Iterable, Literal, Union, cast
from PIL import Image, ImageFile
import fnmatch
import re


PBRChannelMetadata = dict[Literal["r", "g", "b", "a", "animated"], Path | bool]
PBRFileMapping = dict[Path, PBRChannelMetadata]


@plugin_logger()
class PBRConvertor(Plugin):
    normal_suffix = "_n"
    specular_suffix = "_s"

    def __init__(self, rp: Resourcepack):
        super().__init__()
        self.rp = rp
        self.source_dir = rp.get_source_dir()
        self.export_dir = rp.get_export_dir()
        self.rp_files = rp.get_files()

        self.normal_files, self.specular_files, self.metadatas, self.original_files = (
            self.pbr_files_mapping()
        )
        Logger.info("PBRConvertor initialized.")

    def pbr_files_mapping(self):
        normal_files: PBRFileMapping = {}
        specular_files: PBRFileMapping = {}
        metadatas: dict[Path, dict[str, Any]] = {}
        original_files: set[Path] = set()

        for file, metadata in self.rp.get_tex_files_mapping():
            stem = file.stem
            suffix = file.suffix
            if (
                len(stem) >= 4
                and stem[-4] == "_"
                and stem[-3] in ("n", "s")
                and stem[-2] == "_"
                and stem[-1] in ("r", "g", "b", "a")
            ) is False:
                continue

            _file_mcmeta = (
                file.with_stem(stem[:-2]).with_suffix(f"{suffix}.mcmeta").absolute()
            )
            file_mcmeta = _file_mcmeta if _file_mcmeta in self.rp_files else None
            mcmeta = ConfigManager.json_load(file_mcmeta) if file_mcmeta else {}
            is_animated = metadata.get("animated", False) or ("animation" in mcmeta)

            file_target = self.rp.relative_file(
                file.with_stem(file.stem[:-2]), self.source_dir, self.export_dir
            )

            channel_file = cast(
                PBRChannelMetadata, {f"{stem[-1]}": file, "animated": is_animated}
            )

            if stem[-3] == "n":
                if file_target not in normal_files:
                    normal_files[file_target] = {"animated": is_animated}
                normal_files[file_target].update(channel_file)
            else:
                if file_target not in specular_files:
                    specular_files[file_target] = {"animated": is_animated}
                specular_files[file_target].update(channel_file)

            original_files.add(file)
            channel_file_mcmeta = metadata.get("mcmeta", None)
            if channel_file_mcmeta:
                self.rp.exclude_file(channel_file_mcmeta)
                file_mcmeta_target = self.rp.relative_file(
                    _file_mcmeta, self.source_dir, self.export_dir
                )
                metadatas[file_mcmeta_target] = ConfigManager.json_load(
                    channel_file_mcmeta
                )

        return normal_files, specular_files, metadatas, original_files

    @staticmethod
    def images_size_compare(
        images: list[Image.Image] | list[ImageFile.ImageFile],
    ) -> bool:
        if not images:
            return True
        if all(image.size == images[0].size for image in images):
            return True
        else:
            return False

    def merge_channels(self) -> Iterable[tuple[Path, Image.Image]]:
        channel_mapping = {"r": 0, "g": 1, "b": 2, "a": 3}

        for file_target, mapping_data in {
            **self.normal_files,
            **self.specular_files,
        }.items():
            existing_channels: set[str] = set()
            existing_channel_images: dict[str, Image.Image] = {}
            opened_images: list[ImageFile.ImageFile] = []

            try:
                for k, v in mapping_data.items():
                    if not isinstance(v, bool):
                        existing_channels.add(k)
                        _image = Image.open(v)
                        opened_images.append(_image)
                        existing_channel_images[k] = _image

                if not existing_channel_images:
                    Logger.warning(f"No valid channels found for {file_target}")
                    continue

                if not self.images_size_compare(list(existing_channel_images.values())):
                    Logger.error(f"{file_target} is not a valid PBR file")

                base_size = list(existing_channel_images.values())[0].size
                channels = [
                    *[Image.new("L", base_size) for _ in range(3)],
                    Image.new("L", base_size, 255),
                ]

                for existing_channel, image in existing_channel_images.items():
                    index = channel_mapping[existing_channel]

                    _image = (
                        image.convert("RGBA").split()[index]
                        if index != 3 and image.mode != "L"
                        else image.convert("L")
                    )
                    channels[index] = _image

                image_new = Image.merge("RGBA", channels)
                yield file_target, image_new
            finally:
                for image in opened_images:
                    try:
                        image.close()
                    except Exception:
                        pass

    def export(self):
        Logger.info("Exporting PBR files...")
        for file_target, image in self.merge_channels():
            try:
                image.save(file_target)
            except Exception as e:
                Logger.error(f"Failed to save {file_target}: {e}")
            finally:
                image.close()

    def __call__(self):
        self.rp.exclude_files(self.original_files)
        EntryPoint.join(ContentEntryPoint.EXPORT_COPY, EntryPoint.At.AFTER, self.export)


@plugin_logger()
class TrimsConvertor(Plugin):
    trims_path_patterns = [
        re.compile(
            r"^(?:"
            r"assets/minecraft/textures/trims/(?:entity|models|items)(?:/(?:humanoid|humanoid_leggings))?/.*?\.png$"
            r"|"
            r"[^/]*/assets/minecraft/textures/trims/(?:entity|models|items)(?:/(?:humanoid|humanoid_leggings))?/.*?\.png$"
            r")"
        )
    ]

    def __init__(
        self,
        rp: Resourcepack,
        base_trim_palette: Path,
        trim_palettes: dict[str, Path],
        ignore_files: set[str] = set(),
        custom_suffix: str = "",
    ):
        super().__init__()
        self.rp = rp
        self.source_dir = rp.get_source_dir()
        self.rp_tex_files = set(rp.get_tex_files())

        self.imgdata_base_trim_palette = (
            Image.open(base_trim_palette).convert("RGBA").get_flattened_data()
        )
        self.trim_palettes = trim_palettes

        self.ignore_patterns: list[tuple[str, Union[str, re.Pattern[str]]]] = []
        for pattern in ignore_files:
            if "**" in pattern:
                regex_pattern = pattern.replace(".", r"\.").replace("*", ".*")
                self.ignore_patterns.append(("regex", re.compile(regex_pattern)))
            else:
                self.ignore_patterns.append(("glob", pattern))
        self.custom_suffix = custom_suffix
        Logger.info("TrimsConvertor initialized.")

    def imgdata_trim_palettes_mapping(
        self,
    ) -> Iterable[tuple[str, list[int]]]:
        for material, image in zip(
            self.trim_palettes.keys(),
            self.rp.get_textures(list(self.trim_palettes.values())),
        ):
            lut = list(range(256)) * 4
            for base_pixel, target_pixel in zip(
                self.imgdata_base_trim_palette,
                image.convert("RGBA").get_flattened_data(),
            ):
                for i in range(4):
                    lut[cast(tuple, base_pixel)[i] + i * 256] = cast(
                        tuple, target_pixel
                    )[i]

            yield (material, lut)

    def is_ignored(self, remap_trims_file_target: Path) -> bool:
        remap_trims_file_target_str = remap_trims_file_target.as_posix()
        should_ignore = False
        for pattern_type, pattern in self.ignore_patterns:
            if pattern_type == "glob":
                if fnmatch.fnmatch(remap_trims_file_target_str, cast(str, pattern)):
                    should_ignore = True
                    break
            elif pattern_type == "regex":
                if cast(re.Pattern[str], pattern).search(remap_trims_file_target_str):
                    should_ignore = True
                    break
        return should_ignore

    def get_trims_files(self) -> Iterable[Path]:
        for file in self.rp_tex_files:
            file = file.absolute()

            try:
                rel_path = file.relative_to(self.source_dir)
            except ValueError:
                continue

            path_str = rel_path.as_posix()

            if "trims/" not in path_str:
                continue

            if any(pattern.match(path_str) for pattern in self.trims_path_patterns):
                yield file

    def remap_trims(self) -> Iterable[tuple[Path, Image.Image]]:
        for trims_file in self.get_trims_files():
            trims = None
            try:
                trims = Image.open(trims_file).convert("RGBA")

                for material, lut in self.imgdata_trim_palettes_mapping():
                    remap_trims_file_target = self.rp.relative_file(
                        trims_file.with_stem(
                            f"{trims_file.stem}_{material}{self.custom_suffix}"
                        ),
                        self.source_dir,
                        self.rp.export_dir,
                    )

                    if self.is_ignored(remap_trims_file_target):
                        continue

                    remapped_trims = trims.point(lut)

                    yield remap_trims_file_target, remapped_trims

            except Exception as e:
                Logger.error(f"Error processing {trims_file}: {e}")
                continue
            finally:
                if trims:
                    try:
                        trims.close()
                    except Exception:
                        pass

    def export(self):

        def save_image(file_target: Path, image: Image.Image):
            try:
                file_target.parent.mkdir(parents=True, exist_ok=True)
                image.save(file_target)
            except Exception as e:
                Logger.error(f"Failed to save {file_target}: {e}")
            finally:
                image.close()

        Logger.info("Exporting Trims files...")
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(save_image, file_target, image)
                for file_target, image in self.remap_trims()
            ]
            for future in as_completed(futures):
                future.result()

    def __call__(self):
        self.rp.exclude_files(set(self.get_trims_files()))
        EntryPoint.join(ContentEntryPoint.EXPORT_COPY, EntryPoint.At.AFTER, self.export)
