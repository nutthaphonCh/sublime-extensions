import unittest

from iconify.detector import find_tokens, token_at


class DetectorTests(unittest.TestCase):
    def test_detects_component_colon_syntax(self):
        text = '<Icon icon="mdi:home" />'
        tokens = find_tokens(text)
        self.assertEqual([token.icon for token in tokens], ["mdi:home"])
        self.assertEqual(tokens[0].source, "mdi:home")

    def test_detects_bracket_syntax_without_overlapping_uno_match(self):
        tokens = find_tokens('class="icon-[ph--airplane]"')
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].icon, "ph:airplane")
        self.assertEqual(tokens[0].syntax, "bracket")

    def test_detects_simple_uno_syntax(self):
        tokens = find_tokens('class="i-mdi-account-outline"')
        self.assertEqual([token.icon for token in tokens], ["mdi:account-outline"])

    def test_detects_hyphenated_uno_prefix(self):
        tokens = find_tokens('class="i-material-symbols-settings-rounded"')
        self.assertEqual([token.icon for token in tokens], ["material-symbols:settings-rounded"])

    def test_ignores_urls(self):
        self.assertEqual(find_tokens("https://iconify.design/docs"), [])

    def test_applies_document_offset(self):
        token = find_tokens("mdi:home", 120)[0]
        self.assertEqual((token.start, token.end), (120, 128))

    def test_finds_token_at_point(self):
        text = "before mdi:home after"
        token = token_at(text, text.index("home"))
        self.assertIsNotNone(token)
        self.assertEqual(token.icon, "mdi:home")


if __name__ == "__main__":
    unittest.main()
