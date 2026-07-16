import unittest

from vscode_settings.jsonc import loads


class JSONCTests(unittest.TestCase):
    def test_comments_trailing_commas_and_urls(self):
        parsed = loads(
            '''{
                // team setting
                "url": "https://example.com/a//b",
                "escaped": "say \\\"hi\\\" /* text */",
                "punctuation": "keep ,} and ,] inside strings",
                "items": [1, 2,],
            }'''
        )
        self.assertEqual("https://example.com/a//b", parsed["url"])
        self.assertEqual('say "hi" /* text */', parsed["escaped"])
        self.assertEqual("keep ,} and ,] inside strings", parsed["punctuation"])
        self.assertEqual([1, 2], parsed["items"])


if __name__ == "__main__":
    unittest.main()
