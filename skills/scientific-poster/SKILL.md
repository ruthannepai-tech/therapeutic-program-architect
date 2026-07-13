---
name: scientific-poster
description: >-
  Build a presentation-ready scientific conference poster as a single editable
  PowerPoint slide (.pptx), sized to large-format spec (e.g. 48x36"), from
  results and figures the user already has — typically prior project artifacts.
  Use this skill whenever the user mentions preparing, making, building, or
  designing a poster, a conference poster, a research/academic poster, a
  virtual/Zoom poster, or a poster session — even if they don't say "pptx".
  The skill runs an interactive intake so the user shapes the title, key
  message, which figures to show, and the conclusions; lets them pick a color
  scheme or supply institutional branding (logo + palette); and produces the
  poster plus a per-section speaker-notes / talking-points script for virtual
  walkthroughs, an optional QR code, and an automated legibility/contrast check.
  Prefer this over generic slide-making whenever the deliverable is a poster.
---

# Scientific poster builder

This skill turns work the user has already done — figures, results, findings
(most often prior artifacts in the project) — into a single-slide, large-format
`.pptx` poster ready for a conference poster session or a Zoom/virtual
presentation. It also produces the extras that make a poster presentable:
a speaker-notes script, an optional QR code, and a legibility check.

The `.pptx` is one giant slide sized to the poster dimensions. That format is
deliberate: the user can open it in PowerPoint or Keynote and drag, restyle, or
retype anything before printing or screen-sharing. Your job is to give them a
strong, correct, legible starting point — not a locked-down artifact.

## Why interactive intake matters

A poster is an argument, not a data dump. The same set of figures can support
very different posters depending on what the presenter wants the viewer to walk
away believing. So **do not silently auto-generate** from whatever artifacts you
find. Gather the raw material, then ask the user to shape it. The four decisions
that most change the result — get these from the user, don't guess:

1. **The one-sentence takeaway.** What should someone remember after 30 seconds?
   This becomes the spine everything else supports.
2. **Which figures, in what order.** Posters fail by showing too much. 2-5
   figures is typical. Let the user pick and rank.
3. **The conclusions / the ask.** What do they want — collaborators, a job, a
   citation, feedback? The "so what" and next steps.
4. **Look and feel.** Color scheme (preset or custom) and any institutional
   branding (logo, required palette).

## Workflow

### Step 1 — Gather source material

If the user points at prior work, pull it. Prior project artifacts live in the
artifact store, not the workspace — find them with `host.artifacts(search=...)`
or `host.artifacts(project_id=...)`, and resolve figures to local paths with
`host.artifact_path(version_id)` so they can be placed on the poster. Read any
result tables or reports the same way. If the user instead pastes text or points
at files, use those. Come to the intake conversation already knowing what
figures and findings are available — don't make the user list them.

### Step 2 — Interactive intake

Ask the user the four shaping questions above. Use `ask_user` with concrete
options where it helps (e.g. offer the color presets; offer the figures you
found so they can pick). Keep it to a short, focused exchange — you already did
the legwork in Step 1. Confirm:

- Title, authors, affiliation
- The one-sentence takeaway (you'll weave it into the title area or a banner)
- Section list and which figure goes where
- Conclusions and the ask
- Color scheme + branding (logo path, custom palette hex, or a named preset)
- Poster dimensions (default 48x36" landscape, 3 columns) and conference/portal
  size constraints if any
- QR target (preprint / paper / contact / repo) — optional
- Contact line for the footer

Poster sizing note: many conferences and virtual portals specify exact
dimensions or aspect ratios. Ask; don't assume. Common: 48x36" (4:3 landscape),
A0 (46.8x33.1"), 42x42" square for some virtual portals.

### Step 3 — Choose a template

Two templates ship, chosen with `spec["template"]`:

- **`classic`** (default) — clean multi-column poster on a portrait or landscape
  large-format canvas (default 48x36"). Best when the content is moderate and
  you want a calm, traditional look.
- **`magazine`** — a splashy, content-dense, 16:9-friendly layout for a
  wide landscape poster or a Zoom screen-share. Adds a takeaway **subtitle band**
  under the title, a **key-stats ribbon** of headline numbers, filled
  **section-header strips** in two alternating accent colours, **figure
  captions**, and **callout boxes** for the one or two lines you want to pop.
  Reach for this when the user asks for something "splashy", "modern",
  "magazine-style", data-rich, or explicitly 16:9. See
  `references/magazine_template.md`.

Both templates share the same section/figure/QR/notes machinery and both run the
legibility check.

### Step 4a — Draft the content

Condense to poster density. Poster text is not paper text: short phrases,
bullets, and one idea per line. Ground every quantitative claim in real data —
when the material is prior project artifacts, read the actual result tables and
quote their numbers; never invent figures. When you summarize a stat, keep it
unambiguous (e.g. "top allele across all 372 peptides", not a bare count next to
a different denominator).

Poster text budget is not the same as page density, and it differs by template:
`classic` wants roughly 300-800 words total; `magazine` is deliberately denser
but its capacity is bounded by physics, not taste. A 16:9 poster caps at 56" on
the long side (PowerPoint's hard limit — the builder clamps and warns above it),
which leaves a fixed body height. **Content that overflows must be cut or moved,
never shrunk below the legibility floor.** The reliable loop: build, read the
overflow warnings, trim the longest sections to ~4 tight lines each (keeping the
numbers), and rebuild. Wider columns wrap text *less*, so for text-heavy posters
prefer fewer, wider columns (4 at 56") over many narrow ones.

The color presets: `clinical_blue`, `forest`, `maroon`, `slate`, `teal`,
`plum`, `charcoal_gold`, `dark`, and the two-accent magazine palettes
`editorial_teal`, `midnight_coral`, `sage_gold`. For custom or institutional
colors pass a `palette` object (see `references/spec_schema.md`) — the magazine
template also reads an optional `accent2` (second header colour) and
`subtitle_text`.

### Step 4b — Build

### Step 4b — Build

The builder is available two ways. Both run the same code and both emit the
poster plus a legibility report and (if notes were given) a speaker-notes
markdown file.

**Preferred — helper already in your kernel** (loaded with this skill):

```python
spec = { ... }                      # see references/spec_schema.md
out, warnings, report = poster_from_spec(spec, out="poster.pptx")
print(report)
print(warnings)
```

**Or the bundled CLI** (identical result, good for a quick one-off):

```bash
python scripts/build_poster.py spec.json --out poster.pptx
```

If `poster_from_spec` isn't defined (skill loaded without its kernel plugin),
fall back to the CLI, or read `scripts/build_poster.py` and call `build_poster`
directly.

### Step 5 — Verify legibility, then iterate

Always read the legibility report the builder returns. It checks font sizes
against large-format reading-distance floors (title >= 60pt, headings >= 36pt,
body >= 24pt) and text/background contrast against WCAG ratios, and it warns
when a section is likely to overflow its column. These are the failures you
cannot see from the code alone and the user cannot see until the poster is
printed or shared. If it flags contrast or overflow, fix it (darker accent,
shorter text, taller poster, fewer figures) and rebuild — don't hand over a
poster with unresolved warnings without telling the user.

Because there's usually no LibreOffice to rasterize the `.pptx`, verify layout
by reading back shape geometry from the saved file (positions, sizes, that every
image and section landed on-canvas and nothing overlaps the footer). See
`references/verify_layout.md` for a reusable geometry-check snippet.

### Step 6 — Deliver

`save_artifacts` the `.pptx`, the `_speaker_notes.md`, and the
`_legibility.txt`. Tell the user the poster is fully editable in
PowerPoint/Keynote, that the speaker notes are also embedded in the slide's
Notes pane (visible in Presenter view — useful for Zoom), and summarize any
legibility findings you resolved.

## Design principles worth transmitting to the user

- **Readable at 6 feet.** Body text on a printed poster should be legible from a
  couple of paces; that's why the floor is 24pt at large format and why the
  check exists.
- **Figures are the poster.** Text supports figures, not the reverse. A poster
  that's mostly words is a paper on a wall.
- **One takeaway.** If a passerby reads only the title and one figure, they
  should still get the point.
- **The notes carry the depth.** Keep the poster sparse; put the nuance,
  caveats, and detailed methods in the speaker script for the people who stop to
  talk (in person) or in Presenter view (Zoom).

## Virtual / Zoom specifics

For a Zoom poster session the same `.pptx` works: the presenter screen-shares
the single slide and zooms into panels. The speaker notes live in the Notes pane
for Presenter view. Consider a slightly larger body font and fewer, larger
figures for screen-share legibility, and make the QR code a clickable/large
target since remote viewers can't walk up to scan it — sometimes better to also
put the URL as plain text in the footer.
