import tempfile
import unittest
from pathlib import Path

from vscode_settings.eslint import environment_with_node, find_command, find_node


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

    def test_finds_node_installed_by_nvm_without_shell_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            node = home / ".nvm" / "versions" / "node" / "v20.20.1" / "bin" / "node"
            node.parent.mkdir(parents=True)
            node.write_text("#!/bin/sh\n", encoding="utf-8")
            node.chmod(node.stat().st_mode | 0o111)

            self.assertEqual(
                node,
                find_node("osx", which=lambda name: None, home=home),
            )

    def test_prepends_discovered_node_to_subprocess_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            node = home / ".nvm" / "versions" / "node" / "v20.20.1" / "bin" / "node"
            node.parent.mkdir(parents=True)
            node.write_text("#!/bin/sh\n", encoding="utf-8")
            node.chmod(node.stat().st_mode | 0o111)

            environment = environment_with_node(
                "osx",
                environ={"PATH": "/usr/bin:/bin"},
                which=lambda name: None,
                home=home,
            )

            self.assertEqual(str(node.parent), environment["PATH"].split(":")[0])

    def test_prefers_workspace_nvm_version(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "home"
            root = Path(temporary) / "project"
            root.mkdir()
            (root / ".nvmrc").write_text("20\n", encoding="utf-8")
            for version in ("v20.20.1", "v24.14.1"):
                node = home / ".nvm" / "versions" / "node" / version / "bin" / "node"
                node.parent.mkdir(parents=True)
                node.write_text("#!/bin/sh\n", encoding="utf-8")
                node.chmod(node.stat().st_mode | 0o111)

            self.assertEqual(
                home / ".nvm" / "versions" / "node" / "v20.20.1" / "bin" / "node",
                find_node("osx", which=lambda name: None, home=home, root=root),
            )


if __name__ == "__main__":
    unittest.main()
