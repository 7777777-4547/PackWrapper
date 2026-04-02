from packwrapper.content import ContentEntryPoint
from packwrapper.config import ConfigManager
from packwrapper.logger import Logger
from packwrapper.plugin import Plugin, plugin_logger
from packwrapper.utils import EntryPoint
from packwrapper import Resourcepack

from pathlib import Path
from typing import Any, Iterable, Literal, cast
from PIL import Image, ImageFile
import fnmatch
import re


PBRChannelMetadata = dict[Literal["r", "g", "b", "a", "animated"], Path | bool]
PBRFileMapping = dict[Path, PBRChannelMetadata]


class PBRConvertor(Plugin):
    normal_suffix = "_n"
    specular_suffix = "_s"

    def __init__(self, rp: Resourcepack):
        super().__init__()
        self.rp = rp
        self.source_dir = rp.get_source_dir()
        self.export_dir = rp.get_export_dir()
        self.rp_files = rp.get_files()
        self.rp_tex_files_mapping = rp.get_tex_files_mapping()

        self.normal_files, self.specular_files, self.metadatas = (
            self.pbr_files_mapping()
        )
        Logger.info("PBRConvertor initialized.")

    def pbr_files_mapping(self):
        normal_files: PBRFileMapping = {}
        specular_files: PBRFileMapping = {}
        metadatas: dict[Path, dict[str, Any]] = {}

        for file, metadata in self.rp_tex_files_mapping:
            stem = file.stem
            suffix = file.suffix
            if (
                len(stem) >= 4
                and stem[-3] in ("n", "s")
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

            self.rp.exclude_file(file)
            channel_file_mcmeta = metadata.get("mcmeta", None)
            if channel_file_mcmeta:
                self.rp.exclude_file(channel_file_mcmeta)
                file_mcmeta_target = self.rp.relative_file(
                    _file_mcmeta, self.source_dir, self.export_dir
                )
                metadatas[file_mcmeta_target] = ConfigManager.json_load(
                    channel_file_mcmeta
                )

        return normal_files, specular_files, metadatas

    @staticmethod
    def images_size_compare(
        images: list[Image.Image] | list[ImageFile.ImageFile],
    ) -> bool:
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
            for k, v in mapping_data.items():
                if not isinstance(v, bool):
                    existing_channels.add(k)
                    existing_channel_images[k] = Image.open(v)

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

    @plugin_logger
    def export(self):
        Logger.info("Exporting PBR files...")
        for file_target, image in self.merge_channels():
            image.save(file_target)
            image.close()

    def __call__(self):
        super().__call__()
        EntryPoint.join(ContentEntryPoint.EXPORT_COPY, EntryPoint.At.AFTER, self.export)


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
    ):
        super().__init__()
        self.rp = rp
        self.source_dir = rp.get_source_dir()
        self.rp_tex_files = rp.get_tex_files()

        self.imgdata_base_trim_palette = Image.open(
            base_trim_palette
        ).get_flattened_data()
        self.imgdata_trim_palettes_mapping = self.__imgdata_trim_palettes_mapping(
            trim_palettes
        )

        self.trims_files = self.get_trims_files()

        self.ignore_files: list[re.Pattern[str]] = [
            re.compile(fnmatch.translate(file)) for file in ignore_files
        ]
        Logger.info("TrimsConvertor initialized.")

    def __imgdata_trim_palettes_mapping(
        self, trim_palettes: dict[str, Path]
    ) -> Iterable[tuple[str, dict[float | tuple[int, ...], float | tuple[int, ...]]]]:

        for material, file in zip(
            trim_palettes.keys(), self.rp.get_textures(list(trim_palettes.values()))
        ):
            yield (
                material,
                {
                    pixel_base: pixel
                    for pixel_base, pixel in zip(
                        self.imgdata_base_trim_palette,
                        file.convert("RGBA").get_flattened_data(),
                    )
                },
            )

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

    def remap_trims(
        self, custom_suffix: str = ""
    ) -> Iterable[tuple[Path, Image.Image]]:
        for trims_file in self.trims_files:
            trims = Image.open(trims_file)
            imgdata_trims = trims.convert("RGBA").get_flattened_data()

            for material, mapping in self.imgdata_trim_palettes_mapping:
                remap_trims_file_target = self.rp.relative_file(
                    trims_file.with_stem(
                        f"{trims_file.stem}_{material}{custom_suffix}"
                    ),
                    self.source_dir,
                    self.rp.export_dir,
                )
                if any(
                    pattern.search(remap_trims_file_target.absolute().as_posix())
                    for pattern in self.ignore_files
                ):
                    continue

                imgdata_remap_trims = [
                    mapping.get(pixel, pixel) for pixel in imgdata_trims
                ]
                remap_trims = Image.new("RGBA", trims.size)
                remap_trims.putdata(imgdata_remap_trims)

                yield remap_trims_file_target, remap_trims

    @plugin_logger
    def export(self):
        Logger.info("Exporting Trims files...")
        for file_target, image in self.remap_trims():
            image.save(file_target)
            image.close()

    def __call__(self):
        super().__call__()
        EntryPoint.join(ContentEntryPoint.EXPORT_COPY, EntryPoint.At.AFTER, self.export)
