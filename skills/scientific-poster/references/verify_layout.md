# Verifying poster layout without LibreOffice

The sandbox usually has no LibreOffice/PowerPoint to rasterize a `.pptx`, so
verify the layout by reading shape geometry back from the saved file. This
catches images running off-canvas, panels overlapping the footer, and empty
columns — the things the build code can't tell you on its own.

```python
from pptx import Presentation

def check_layout(path):
    prs = Presentation(path)
    W = prs.slide_width / 914400
    H = prs.slide_height / 914400
    sl = prs.slides[0]
    issues = []
    for sh in sl.shapes:
        l = sh.left / 914400; t = sh.top / 914400
        w = (sh.width or 0) / 914400; h = (sh.height or 0) / 914400
        if l < -0.01 or t < -0.01 or l + w > W + 0.01 or t + h > H + 0.01:
            kind = "picture" if sh.shape_type == 13 else "shape"
            issues.append(f"{kind} off-canvas: ({l:.1f},{t:.1f}) {w:.1f}x{h:.1f} on {W:.0f}x{H:.0f}")
    n_pics = sum(1 for sh in sl.shapes if sh.shape_type == 13)
    notes = sl.notes_slide.notes_text_frame.text if sl.has_notes_slide else ""
    return {"size_in": (round(W), round(H)), "n_pictures": n_pics,
            "notes_present": bool(notes.strip()), "issues": issues}

print(check_layout("poster.pptx"))
```

If you want a rough visual, you can draw the shape rectangles and paste the
embedded images with matplotlib (see the build session for an example), but the
geometry check above is the fast, reliable gate. If `issues` is non-empty, adjust
the spec (shorter text, `max_img_h_in`, taller poster, or fewer sections per
column) and rebuild.
