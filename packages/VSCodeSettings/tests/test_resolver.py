import tempfile
import unittest
from pathlib import Path

from vscode_settings.resolver import SettingsResolver, effective_settings, language_id


class ResolverTests(unittest.TestCase):
    def test_nearest_workspace_and_language_override(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".vscode").mkdir()
            (root / ".vscode" / "settings.json").write_text(
                '''{
                    "editor.tabSize": 2,
                    "[typescript]": {"editor.tabSize": 4,},
                }''',
                encoding="utf-8",
            )
            source = root / "src" / "main.ts"
            source.parent.mkdir()
            source.write_text("", encoding="utf-8")

            resolved = SettingsResolver().resolve(str(source))
            self.assertIsNotNone(resolved)
            self.assertEqual(root.resolve(), resolved.root)
            self.assertEqual("typescript", resolved.language)
            self.assertEqual(4, resolved.values["editor.tabSize"])

    def test_combined_language_override(self):
        values = effective_settings(
            {"editor.tabSize": 2, "[javascript][typescript]": {"editor.tabSize": 3}},
            "typescript",
        )
        self.assertEqual(3, values["editor.tabSize"])

    def test_language_ids(self):
        self.assertEqual("typescriptreact", language_id(Path("component.tsx")))
        self.assertEqual("javascript", language_id(Path("script.mjs")))


if __name__ == "__main__":
    unittest.main()
