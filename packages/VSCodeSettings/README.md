# VS Code Settings for Sublime Text

Uses the nearest `.vscode/settings.json` as a shared workspace-policy source for
Sublime Text. The file is parsed as JSONC, including comments and trailing
commas, and VS Code language overrides such as `[typescript]` are applied.

## Supported settings

| VS Code | Sublime Text |
| --- | --- |
| `editor.tabSize` | `tab_size` |
| `editor.insertSpaces` | `translate_tabs_to_spaces` |
| `editor.detectIndentation` | `detect_indentation` |
| `editor.wordWrap` | `word_wrap` |
| `editor.wordWrapColumn` | `wrap_width` |
| `editor.rulers` | `rulers` |
| `editor.renderWhitespace` | `draw_white_space` |
| `files.trimTrailingWhitespace` | `trim_trailing_white_space_on_save` |
| `files.insertFinalNewline` | `ensure_newline_at_eof_on_save` |

When `editor.codeActionsOnSave.source.fixAll.eslint` is `true`, `explicit`, or
`always`, the package runs the workspace-local `node_modules/.bin/eslint --fix`
after saving supported JavaScript, TypeScript, Vue, or Svelte files. It never
downloads a command or package. Sublime Text does not expose VS Code's save
reason, so `explicit` applies to every Sublime save event; this matches normal
manual-save workflows, while teams using auto-save should account for it.

`editor.defaultFormatter` and extension-specific settings are intentionally not
pretended to be editor-native settings. A formatter or feature needs a Sublime
adapter before it can be honored. In particular, `editor.formatOnSave: false`
is naturally preserved because this package does not invoke a formatter.

## Installation

Link or copy this directory to Sublime Text's `Packages/VSCodeSettings`
directory. Open any file below a workspace containing `.vscode/settings.json`.
The status bar shows the workspace and language policy currently applied.

Use **VS Code Settings: Reload Workspace Settings** from the Command Palette
after an external tool changes the settings file.

## Package settings

Open **Preferences -> Package Settings -> VS Code Settings -> Settings** to
disable synchronization, ESLint fix-on-save, or status text locally. These
machine-local switches do not alter team policy in `.vscode/settings.json`.

## Development

```bash
python3 -m unittest discover -s tests -v
```
