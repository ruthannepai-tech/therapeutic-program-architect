# Poster spec schema

The builder takes a single JSON/dict `spec`. Only `title` and `sections` are
required; everything else has a sensible default.

## Top-level fields

| field | type | default | notes |
|---|---|---|---|
| `title` | str | (required) | Poster title, shown large in the title bar. |
| `sections` | list | (required) | See below. |
| `authors` | str | — | Author line under the title. |
| `affiliation` | str | — | Affiliation / event line under authors. |
| `palette` | str or object | `"clinical_blue"` | Preset name or custom object (below). |
| `width_in` | number | 48 | Poster width in inches. |
| `height_in` | number | 36 | Poster height in inches. |
| `columns` | int | 3 | Number of body columns. |
| `margin_in` | number | 1.0 | Outer margin. |
| `gutter_in` | number | 0.8 | Gap between columns. |
| `title_h_in` | number | 4.5 | Height of the title bar. |
| `footer_h_in` | number | 2.5 | Height of the footer bar. |
| `title_pt` | int | 80 | Title font size. Floor for check: 60. |
| `author_pt` | int | 40 | |
| `affil_pt` | int | 30 | |
| `head_pt` | int | 44 | Section heading size. Floor: 36. |
| `body_pt` | int | 32 | Body text size. Floor: 24. |
| `footer_pt` | int | 26 | |
| `max_img_h_in` | number | 6.5 | Max height any single figure is scaled to. |
| `logo` | str | — | Path to a logo image placed in the title bar (left). |
| `qr_url` | str | — | If set, a QR code is generated and placed in the footer. |
| `footer_text` | str | — | Contact / repo / event line in the footer. |
| `speaker_notes` | str | — | Free text; embedded in the slide Notes pane AND written to `<out>_speaker_notes.md`. |

## Section object

Each entry in `sections`:

| field | type | notes |
|---|---|---|
| `title` | str | Section heading (e.g. "Methods"). Optional but usual. |
| `body` | str | Body text. Use `\n` to separate lines/bullets; start lines with `•` for bullets. |
| `image` | str | Path to a figure to place under the body. Aspect ratio preserved. |
| `column` | int | 0-indexed target column. If omitted, sections fill columns round-robin. |

Sections are placed top-to-bottom within their column in list order.

## Custom / institutional palette object

Instead of a preset name, pass an object with these six roles (all hex strings):

```json
"palette": {
  "primary":          "#1F3A5F",   // title bar + footer background
  "accent":           "#2E86C1",   // section headings + panel borders
  "panel_bg":         "#FFFFFF",   // section panel fill
  "page_bg":          "#EAF0F6",   // poster background
  "text":             "#1A1A1A",   // body text
  "panel_title_text": "#FFFFFF"    // text on the primary bar (title/footer)
}
```

Any roles you omit fall back to the `clinical_blue` defaults. The legibility
check will tell you if your `text`-on-`panel_bg`, `accent`-on-`panel_bg`, or
`panel_title_text`-on-`primary` contrast is too low.

## Preset names

`clinical_blue`, `forest`, `maroon`, `slate`, `teal`, `plum`, `charcoal_gold`,
`dark`. All are tuned to pass the contrast floors on white panels (the `dark`
preset uses dark panels with light text).

## Outputs

`build_poster(spec, out)` / `poster_from_spec(spec, out)` returns
`(out_path, warnings, report)` and writes:

- `<out>` — the poster `.pptx`
- `<out_stem>_legibility.txt` — the legibility & contrast report
- `<out_stem>_speaker_notes.md` — the talking-points script (only if `speaker_notes` given)
- `<out_stem>_qr.png` — the QR image (only if `qr_url` given)


## Magazine-template fields (template = "magazine")

See `references/magazine_template.md` for the full guide. Additional fields:

| field | type | notes |
|---|---|---|
| `template` | str | `"magazine"` to select this template (default `"classic"`). |
| `subtitle` | str | One-line takeaway shown under the title. |
| `stats` | list | `[{"value": "...", "label": "..."}]` — key-numbers ribbon. |
| `sections[].caption` | str | Caption printed under a figure. |
| `sections[].callout` | str | Highlighted line (white on `accent2`). |
| `sections[].accent` | str | `"accent"` or `"accent2"` — overrides the header-strip colour. |
| palette `accent2` | hex | Second header/callout colour (magazine palettes set it). |
| palette `subtitle_text` | hex | Subtitle colour on the title band. |

Note: any side > 56 in is clamped to 56 in (PowerPoint limit) with a warning.
