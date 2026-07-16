import unittest
from unittest.mock import patch

from iconify.api import IconifyAPI, IconifyError


class APITests(unittest.TestCase):
    def test_svg_rejects_non_svg_response(self):
        api = IconifyAPI()
        with patch.object(api, "_get", return_value=b'{"error":"not_found"}'):
            with self.assertRaises(IconifyError):
                api.svg("mdi", "missing", 18, "#fff")

    def test_search_filters_invalid_items_and_limit(self):
        api = IconifyAPI()
        payload = b'{"icons":["mdi:home",42,"mdi:house"]}'
        with patch.object(api, "_get", return_value=payload) as get:
            icons = api.search("home", limit=1, prefix="mdi")
        self.assertEqual(icons, ["mdi:home"])
        get.assert_called_once_with(
            "/search",
            {"query": "home", "limit": 1, "prefix": "mdi"},
        )


if __name__ == "__main__":
    unittest.main()
