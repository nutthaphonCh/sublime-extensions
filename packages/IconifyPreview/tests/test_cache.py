import tempfile
import unittest

from iconify.cache import IconCache


class CacheTests(unittest.TestCase):
    def test_keys_are_stable_and_file_safe(self):
        first = IconCache.key("mdi:home", 18, "#ffffff")
        second = IconCache.key("mdi:home", 18, "#ffffff")
        different = IconCache.key("mdi:home", 19, "#ffffff")
        self.assertEqual(first, second)
        self.assertNotEqual(first, different)
        self.assertRegex(first, r"^[a-f0-9]{64}$")

    def test_search_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = IconCache(directory)
            cache.write_search("mdi:home", 10, ["mdi:home", "mdi:home-outline"])
            self.assertEqual(
                cache.read_search("mdi:home", 10),
                ["mdi:home", "mdi:home-outline"],
            )

    def test_invalid_search_cache_is_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = IconCache(directory)
            path = cache.search_path("mdi:home", 10)
            path.write_text('{"not": "a list"}', encoding="utf-8")
            self.assertIsNone(cache.read_search("mdi:home", 10))


if __name__ == "__main__":
    unittest.main()
