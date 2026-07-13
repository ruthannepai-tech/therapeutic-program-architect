# Magazine template

A splashy, content-dense layout for wide 16:9 posters and Zoom screen-shares.
Select it with `spec["template"] = "magazine"`.

## What it adds over the classic template

| Feature | Spec field | Notes |
|---|---|---|
| Takeaway subtitle band | `subtitle` | One-line "so what", shown under the title in `subtitle_text` colour. |
| Key-stats ribbon | `stats: [{value,label}]` | Row of headline-number cards under the title. 3-6 cards reads best. |
| Two-accent header strips | palette `accent` + `accent2` | Section headers are filled strips, alternating the two accents (override per section with `accent: "accent"|"accent2"`). |
| Figure captions | `sections[].caption` | Small text printed under a figure. |
| Callout boxes | `sections[].callout` | A short line rendered white-on-`accent2` — use for the punchline of a section. |

Two-accent palettes tuned for this template: `editorial_teal`,
`midnight_coral`, `sage_gold`. Any classic palette works too; the builder
falls back `accent2 → accent` and `subtitle_text → panel_title_text` if unset.

## Sizing — the 56" wall

PowerPoint refuses a slide larger than **56 inches** on any side. The builder
clamps to that and adds a warning (print shops enlarge the PDF from there). So a
true-16:9 magazine poster maxes out at **56 x 31.5"**. That fixed size, minus
the title band, stats ribbon, and footer, leaves roughly **24" of body height**.

This is a hard capacity, and it is the single thing that most often bites:
content that would be fine on a 6-foot printed poster does not fit 24" of body
at a 24pt floor. When the build reports `Column N content exceeds body height`:

1. **Trim, don't shrink.** Cut each long section to ~4 tight lines. Keep every
   number; drop connective prose. The speaker notes hold the detail.
2. **Rebalance columns.** Spread figure-bearing sections apart; a greedy
   "add each section to the currently-shortest column" pass balances well.
3. **Fewer, wider columns.** Narrow columns wrap text into more lines and make
   overflow *worse*. For text-heavy content, 4 columns at 56" beats 5-6.
4. **Shave figure height** (`max_img_h_in`) a little — the figures are usually
   the tallest single elements.
5. Only after the above, consider a taller (non-16:9) canvas.

A practical recipe that fits ~10 dense sections + 4 figures at the legibility
floor: `width_in=56, height_in=31.5, columns=4, body_pt=24, max_img_h_in≈3.4`,
sections trimmed to ≤4 lines, greedy-balanced across the columns.

## Minimal magazine spec

```json
{
  "template": "magazine",
  "title": "...", "subtitle": "one-line takeaway",
  "authors": "...", "affiliation": "...",
  "palette": "editorial_teal",
  "width_in": 56, "height_in": 31.5, "columns": 4,
  "stats": [
    {"value": "1,800", "label": "predictions \u00b7 55 strong"},
    {"value": "\u221249%", "label": "protease sites removed"}
  ],
  "sections": [
    {"title": "Background", "body": "line\\nline\\nline"},
    {"title": "Key Result", "image": "figA.png",
     "caption": "what the figure shows", "callout": "the punchline"}
  ],
  "qr_url": "https://...", "footer_text": "...",
  "speaker_notes": "[Background] ... [Ask] ..."
}
```

## Verify

Same as classic: read the legibility report (the magazine builder reports the
sizes it actually used, and checks white-on-accent header contrast), then run
the geometry check in `references/verify_layout.md` — with a wide poster it's
worth confirming `offcanvas == 0` and that no column's lowest panel crosses into
the footer.
