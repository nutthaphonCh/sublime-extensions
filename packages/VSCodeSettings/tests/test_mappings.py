import unittest

from vscode_settings.mappings import eslint_fix_requested, sublime_settings


class MappingTests(unittest.TestCase):
    def test_maps_editor_and_file_settings(self):
        mapped = sublime_settings(
            {
                "editor.tabSize": 2,
                "editor.insertSpaces": True,
                "editor.detectIndentation": False,
                "editor.wordWrap": "on",
                "editor.wordWrapColumn": 100,
                "editor.rulers": [80, {"column": 120, "color": "#fff"}],
                "editor.renderWhitespace": "all",
                "files.trimTrailingWhitespace": True,
                "files.insertFinalNewline": True,
            }
        )
        self.assertEqual(2, mapped["tab_size"])
        self.assertTrue(mapped["translate_tabs_to_spaces"])
        self.assertFalse(mapped["detect_indentation"])
        self.assertTrue(mapped["word_wrap"])
        self.assertEqual([80, 120], mapped["rulers"])
        self.assertEqual("all", mapped["draw_white_space"])
        self.assertTrue(mapped["trim_trailing_white_space_on_save"])
        self.assertTrue(mapped["ensure_newline_at_eof_on_save"])

    def test_eslint_explicit_is_enabled(self):
        self.assertTrue(
            eslint_fix_requested(
                {"editor.codeActionsOnSave": {"source.fixAll.eslint": "explicit"}}
            )
        )
        self.assertFalse(
            eslint_fix_requested(
                {"editor.codeActionsOnSave": {"source.fixAll.eslint": "never"}}
            )
        )


if __name__ == "__main__":
    unittest.main()

