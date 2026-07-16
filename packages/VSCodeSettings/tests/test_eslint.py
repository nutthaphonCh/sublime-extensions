import tempfile
import unittest
from pathlib import Path

from vscode_settings.eslint import find_command


class ESLintTests(unittest.TestCase):
    def test_prefers_workspace_local_executable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            executable = root / "node_modules" / ".bin" / "eslint"
            executable.parent.mkdir(parents=True)
            executable.write_text("#!/bin/sh\n", encoding="utf-8")
            executable.chmod(executable.stat().st_mode | 0o111)

            self.assertEqual(
                [str(executable)],
                find_command(root, "osx", which=lambda name: "/global/eslint"),
            )

    def test_falls_back_without_downloading(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertEqual(
                ["/global/eslint"],
                find_command(root, "linux", which=lambda name: "/global/eslint"),
            )
            self.assertIsNone(find_command(root, "linux", which=lambda name: None))


if __name__ == "__main__":
    unittest.main()
