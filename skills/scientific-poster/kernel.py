"""Auto-loaded helper for the scientific-poster skill.

Exposes `poster_from_spec(spec, out="poster.pptx")` -> (out_path, warnings, report).
It executes the bundled scripts/build_poster.py to get the real builder, so there
is a single source of truth for the layout engine.
"""

def poster_from_spec(spec, out="poster.pptx"):
    """Build a poster .pptx from a spec dict. Returns (out_path, warnings, report_str).

    Requires python-pptx, pillow, qrcode in the active env:
        manage_packages(mode="install", environment=..., packages=["python-pptx","pillow","qrcode"])
    See SKILL.md and references/spec_schema.md for the spec fields and palette names.
    """
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    script = os.path.join(here, "scripts", "build_poster.py")
    ns = {}
    with open(script) as f:
        code = compile(f.read(), script, "exec")
    exec(code, ns)
    return ns["build_poster"](spec, out=out)


def poster_palettes():
    """Return the dict of built-in color palettes (name -> hex color roles)."""
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    script = os.path.join(here, "scripts", "build_poster.py")
    ns = {}
    with open(script) as f:
        exec(compile(f.read(), script, "exec"), ns)
    return ns["PALETTES"]
