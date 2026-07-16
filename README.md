# Sublime Extensions

Sublime Text packages maintained in one repository:

- **IconifyPreview** — inline and hover previews plus completions for Iconify
  icon names.
- **VSCodeSettings** — consumes the nearest `.vscode/settings.json` as shared
  workspace policy.

## Install with Package Control

Add this repository URL through **Package Control: Add Repository**:

```text
https://raw.githubusercontent.com/nutthaphonCh/sublime-extensions/main/repository.json
```

Then run **Package Control: Install Package** and select `IconifyPreview` or
`VSCodeSettings`.

Equivalent Package Control user settings:

```json
{
  "repositories": [
    "https://raw.githubusercontent.com/nutthaphonCh/sublime-extensions/main/repository.json"
  ]
}
```

## Release

Build both GitHub Release assets from the package directories:

```bash
python3 scripts/build_packages.py
```

Create a semantic-version GitHub release and upload both files from `dist/`.
The Package Control repository manifest resolves each package from its matching
`.sublime-package` release asset.
