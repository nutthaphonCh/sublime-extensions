# Iconify Preview for Sublime Text

Inline previews, hover previews, and remote completions for
[Iconify](https://iconify.design/) icon names in Sublime Text 4.

## Features

- Shows a small icon immediately after recognized Iconify names.
- Shows a larger preview and a link to the icon set on hover.
- Completes icon names after **prefix:** and inside UnoCSS bracket syntax.
- Fetches icons from the public Iconify API without a Node.js dependency.
- Caches SVG, PNG, and search responses in Sublime's cache directory.
- Performs network and rendering work outside Sublime's UI thread.

Recognized syntax:

~~~tsx
<Icon icon="mdi:home" />
const icon = "material-symbols:settings-rounded"
~~~

~~~html
<span class="i-mdi-account"></span>
<span class="i-material-symbols-settings-rounded"></span>
<span class="icon-[ph--airplane]"></span>
~~~

## Installation

This repository is currently a development package. Copy or clone the
**IconifyPreview** directory into Sublime Text's **Packages** directory:

- macOS: ~/Library/Application Support/Sublime Text/Packages/
- Linux: ~/.config/sublime-text/Packages/
- Windows: %APPDATA%\Sublime Text\Packages\

Sublime reloads unpacked packages automatically. Run **Iconify: Refresh
Previews** from the Command Palette if an already-open view does not refresh.

## Rendering requirements

Sublime's minihtml supports PNG, JPG, and GIF images but not SVG. The package
therefore downloads Iconify SVG and converts it to a cached PNG.

- macOS uses the bundled universal resvg 0.44.0 binary.
- Linux and Windows use the first available command from resvg,
  rsvg-convert, ImageMagick (magick), or Inkscape.

If previews are missing, open Sublime's console and look for an
**IconifyPreview:** message. Completion still works without an SVG renderer.

## Settings

Open **Preferences → Package Settings → Iconify Preview → Settings**.

~~~json
{
    "inline_preview": true,
    "inline_size": 18,
    "hover_preview": true,
    "hover_size": 96,
    "color": "auto",
    "completions": true
}
~~~

Settings may be overridden per project or view by adding the
**iconify_preview.** prefix:

~~~json
{
    "settings": {
        "iconify_preview.inline_size": 20,
        "iconify_preview.color": "#7c3aed"
    }
}
~~~

## Privacy and network behavior

The package sends recognized icon names and completion search terms to the
configured **api_url**, which defaults to https://api.iconify.design. Source
code and file contents are not uploaded. Set **enabled** or **completions** to
false if that behavior is not desired.

## Current limitations

- The first preview of an icon requires network access.
- UnoCSS i- syntax is ambiguous when an icon-set prefix contains hyphens.
  Common multi-part prefixes are recognized; prefix:name and bracket syntax
  are unambiguous and recommended for uncommon collections.
- Animated SVG icons are rendered as a static PNG frame.

## Development

Core tests do not require Sublime:

~~~bash
python3 -m unittest discover -s tests -v
~~~

The package is licensed under the MIT License.

The bundled resvg executable is distributed under the Mozilla Public License
2.0. Its license text is included under **THIRD_PARTY_LICENSES**, and its
upstream source is available from https://github.com/linebender/resvg.
