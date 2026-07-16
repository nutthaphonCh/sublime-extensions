import base64
import struct
import sys
import tempfile
import unittest
from pathlib import Path

from iconify.cache import IconCache
from iconify.renderer import IconRenderer, png_data_uri


class FakeAPI:
    def __init__(self):
        self.calls = 0

    def svg(self, prefix, name, size, color):
        self.calls += 1
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
            'viewBox="0 0 24 24"><path fill="' + color + '" '
            'd="M4 4h16v16H4z"/></svg>'
        ).encode("utf-8")


class DataURITests(unittest.TestCase):
    def test_png_is_embedded_as_data_uri(self):
        data = b"\x89PNG\r\n\x1a\nexample"
        with tempfile.NamedTemporaryFile(suffix=".png") as image:
            image.write(data)
            image.flush()
            uri = png_data_uri(Path(image.name))

        prefix, encoded = uri.split(",", 1)
        self.assertEqual("data:image/png;base64", prefix)
        self.assertEqual(data, base64.b64decode(encoded))


@unittest.skipUnless(sys.platform == "darwin", "bundled renderer test is for macOS")
class RendererTests(unittest.TestCase):
    def test_bundled_resvg_creates_and_caches_rgba_png(self):
        with tempfile.TemporaryDirectory() as directory:
            api = FakeAPI()
            renderer = IconRenderer(IconCache(directory), api)
            first = renderer.render("test:square", 32, "#7c3aed")
            second = renderer.render("test:square", 32, "#7c3aed")

            data = first.read_bytes()
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            width, height, bit_depth, color_type = struct.unpack(
                ">IIBB", data[16:26]
            )
            self.assertEqual((width, height), (32, 32))
            self.assertEqual((bit_depth, color_type), (8, 6))
            self.assertEqual(first, second)
            self.assertEqual(api.calls, 1)


if __name__ == "__main__":
    unittest.main()
