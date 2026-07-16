from __future__ import annotations

import os
import platform
import shutil
import subprocess
from pathlib import Path

from .api import IconifyAPI
from .cache import IconCache


class RenderError(RuntimeError):
    pass


class IconRenderer:
    def __init__(self, cache: IconCache, api: IconifyAPI) -> None:
        self.cache = cache
        self.api = api

    def render(self, icon: str, size: int, color: str) -> Path:
        prefix, separator, name = icon.partition(":")
        if not separator or not prefix or not name:
            raise RenderError(f"Invalid Iconify name: {icon}")
        svg_path, png_path = self.cache.paths(icon, size, color)
        if png_path.is_file() and png_path.stat().st_size > 0:
            return png_path

        if not svg_path.is_file() or svg_path.stat().st_size == 0:
            self.cache.atomic_write(svg_path, self.api.svg(prefix, name, size, color))
        self._convert(svg_path, png_path, size)
        if not png_path.is_file() or png_path.stat().st_size == 0:
            raise RenderError("SVG renderer did not create a PNG")
        return png_path

    def _convert(self, source: Path, destination: Path, size: int) -> None:
        errors: list[str] = []
        for command, generated in self._commands(source, destination, size):
            try:
                result = subprocess.run(
                    command,
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    timeout=15,
                )
            except (OSError, subprocess.SubprocessError) as error:
                errors.append(str(error))
                continue
            if result.returncode != 0:
                errors.append(result.stderr.decode("utf-8", "replace").strip())
                continue
            if generated != destination and generated.is_file():
                os.replace(generated, destination)
            if destination.is_file():
                return
        detail = next((item for item in errors if item), "no supported SVG renderer found")
        raise RenderError(detail)

    @staticmethod
    def _commands(source: Path, destination: Path, size: int):
        package_root = Path(__file__).resolve().parent.parent
        bundled_resvg = package_root / "bin" / "macos-universal" / "resvg"
        if platform.system() == "Darwin" and bundled_resvg.is_file():
            yield [
                str(bundled_resvg),
                str(source),
                str(destination),
                "--width",
                str(size),
                "--height",
                str(size),
            ], destination

        resvg = shutil.which("resvg")
        if resvg:
            yield [resvg, str(source), str(destination), "--width", str(size), "--height", str(size)], destination

        rsvg = shutil.which("rsvg-convert")
        if rsvg:
            yield [rsvg, "-w", str(size), "-h", str(size), "-o", str(destination), str(source)], destination

        magick = shutil.which("magick")
        if magick:
            yield [magick, str(source), "-background", "none", "-resize", f"{size}x{size}", str(destination)], destination

        inkscape = shutil.which("inkscape")
        if inkscape:
            yield [
                inkscape,
                str(source),
                "--export-type=png",
                f"--export-filename={destination}",
                f"--export-width={size}",
                f"--export-height={size}",
            ], destination
