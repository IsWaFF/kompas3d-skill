---
name: kompas-3d
description: Drive KOMPAS-3D v25 (native Linux build, running in a distrobox) from Python to build 2D fragments and drawings (segments, circles, arcs, polygons, linear/radial/diametral/angle dimensions, colour fills, ornaments, flat parts), export PNG, and troubleshoot its launch on Wayland. Use whenever the user mentions КОМПАС/Компас/KOMPAS, чертёж, фрагмент (.frw/.cdw), or an engineering-graphics (черчение) task.
---

# KOMPAS-3D automation

## Setup this skill assumes
- KOMPAS-3D v25 (tested: Home 25.0.1.2738) in a distrobox, default name `kompas-box` (Ubuntu 24.04), installed under `/opt/ascon/kompas3d-v25`. Override with `KOMPAS_BOX` / `KOMPAS_DIR`. Only Qt's **xcb** plugin ships, so KOMPAS always runs through X11.
- Start it with **`kompas-nested`** (the launcher next to this skill's repo): KOMPAS inside Xephyr + openbox. On swayfx 0.6, KOMPAS's context panel (an XWayland `window_type=utility` popup that maps/unmaps quickly) aborts the compositor and kills the whole session. Nested, the compositor sees one ordinary window. On sway, never run `swaymsg 'for_window … a, b'` at runtime: the commas split it into separate commands. Edit the config file and `swaymsg reload` instead.
- The API needs a real display. Under Xvfb the licence window never finishes and the API port never opens.
- Ask the user where their files and assignment PDFs are. Don't guess paths.

## Connecting
- `ksapi.GetKompas()` reads `/proc/net/tcp`, looks for a listening socket owned by a process named `kHome` and connects to it. It returns `None` while KOMPAS is starting (the port opens after the licence check), or if KOMPAS was started via the `kompas-home-v25` symlink (different process name). `OpenKompas()` hardcodes `kKompas`, which Home lacks. So always attach to a running instance and ask the user to start KOMPAS.
- Run scripts with `scripts/run.sh /path/script.py [args]`. It enters the box, sets PYTHONPATH to KOMPAS `Bin` plus this skill's `scripts/`, and applies a 120 s timeout (`T=300` raises it).
- Put scratch scripts under `$HOME`, which is shared with the box (`$CLAUDE_JOB_DIR/tmp` if set).
- Helpers: `import ks`. The full list is in `scripts/ks.py`:
  - documents: `ks.new_fragment()`, `ks.use(doc)`, `ks.info()`, `ks.clear()`;
  - geometry: `seg`, `pt`, `axes`, `circle`, `arc`, `polygon`, `text`;
  - dimensions: `rdim`, `ddim`, `ldim`, `adim`;
  - fills: `fill`, `rgb`;
  - checks and output: `overlaps`, `export_png`, `save`.
- On import `ks` targets the active document only if it is 2D. `GetActiveDocument()` can return a hidden document (e.g. a template).
- **Never draw into a document the user didn't ask you to change.** Use `ks.new_fragment()` for experiments.
- The API mirrors API7 (IDrawingContainer, ISymbols2DContainer …). To list a class's methods: `awk '/^class IArc\(/{f=1;next} /^class /{f=0} f&&/def [A-Z]/' /opt/ascon/kompas3d-v25/Bin/ksapi.py`. Constants are in `constants.py` (grep the Russian comments). SDK docs are under `SDK/` in the install dir.
- `collection.GetItem(i)` returns a bare `IDrawingObject`. Cast it before use: `ksapi.ILineSegment(item)`, `ksapi.ICircle(item)`, `ksapi.IArc(item)`.

## Workflow for an assignment
1. Read the PDF with `scripts/pdf_images.py <pdf> <outdir> [pages]`. It needs a venv with pypdf and pillow, plus shapely if you will do geometry. Look at every figure image with Read.
2. **Read the figure as a drawing, not as a picture.** Work out the real part outline before coding:
   - Decide whether notches or slots are *closed at the bottom* (a flat bottom at radius R) or cut through. "Disk R60 with 6 notches to R44" is easy to misread as "ring R44–R60 with through slots".
   - Check whether an outer edge **continues across** a notch, and **compare line thickness in pixels** (measure dark-pixel runs per column). A thin line (~2 px against ~6 px for the contour) crossing a notch means the notch is open: thick sides, a thick bottom, and one `ksCSThin` segment across it.
   - Decide whether lobes join the base circle directly or through small fillets.
   - Take missing sizes from the pixels: px/mm = diameter_px / diameter_mm of a known circle, then measure. Tell the user which sizes are estimated.
3. Build with **final, trimmed geometry**. Compute the exact arcs and segments of the contour yourself (intersection angles and so on). Never leave full circles or overlapping pieces that a student would remove with «Усечь кривую». No duplicate objects.
4. Dimension it. A common course style:
   - radial dims are half (`SetDimensionType(True)`) with text on a shelf (`rdim(..., shelf=(x, y))`);
   - holes repeated N times get `under='N отв.'` / `prefix='N отв. '`;
   - a square size uses `ldim(..., sign=2)` (□);
   - concentric diameters through a crowded centre are usually half dims (`ddim(..., half=True)`).

   Copy the figure dimension by dimension.
5. `ks.overlaps()` must return `[]`. Users check drawings for «наслоения»: collinear overlapping segments, or arcs and circles on the same circle.
6. `ks.save('/abs/path.frw')` right after building, because crashes lose unsaved work. A new document needs a path, otherwise KOMPAS opens a modal Save dialog and the script hangs.
7. Export with `ks.export_png(path)` and **look at it** before reporting. Fix dimension text sitting on lines and similar problems.
8. For a report, crop PNGs per task and save them next to the .frw.

## Gotchas (verified on v25)
- **Arcs:** `arc(xc, yc, r, a1, a2)` runs CCW from a1 to a2. The meaning of `SetDirection` is unreliable: `True` has drawn the clockwise complement while Angle1/Angle2 still read back correctly. The helper checks the midpoint `GetX3/GetY3` and flips if needed. **Verify arcs by X3/Y3, never by the angles.** A complement arc stacks a thick line and an axial line on the same circle, which users see as «наслоения».
- **Angle dims:** use `sc.GetAngleDimensions().Add(c.ksDrADimension)`; other values return None.
  - **Bind the dim to two segments** (`SetBaseObject1/2`) and set X3/Y3 for the arc and text position. That is what `adim(line1, line2, x, y)` does.
  - KOMPAS measures **CCW from line1's direction to line2's** (direction = the segment's start → end). Swap the arguments if you get the reflex angle. X3/Y3 does not choose the angle.
  - With bare X1/Y1/X2/Y2 points, the second ray's angle is taken from the sheet origin, not the vertex. The values are wrong unless the vertex is at (0, 0). Angle1/Angle2 setters are ignored.
- **Diametral dims:**
  - `IDiametralDimension` has no ShelfX/Y, and `SetShelfAngle`/`SetShelfLength` don't stick (they read back 0).
  - To move the text along the dimension line: `IDimensionParams.SetTextType(ksDimTManual)` + `SetTextPos(mm from the line's far end)`. That is `ddim(text_at=)`.
  - Small circles get a leader and shelf automatically. `SetTextOnLine(ksDTPOnShelf)` + `SetTextPos` lengthens the leader (`ddim(leader=)`), and `SetShelfDirection(ksLSLeft/Right)` picks the side.
  - Prefix: `IDimensionText.GetPrefix().SetStr('4 отв. ')`.
  - `SetDimensionType(False)` is a full dim with two arrows. `True` is a half dim: one arrow, and the line breaks just past the centre.
- **Dimension text masks the lines under it** (a white gap in PNG export). Keep texts off contours. The default spot of a half-dim text is near the middle of the line, often right on an inner circle.
- Colours are COLORREF `0xBBGGRR`. Use `ks.rgb(r, g, b)`.
- Raster export is greyscale unless `SetColorType(1)`. If the file exists, it raises a modal «файл уже существует» on the user's screen, so delete it first (the helper does).
- `MakeEncloseContours` returns an IDrawingGroup. Pass `grp.GetObjects([0])` to `AddBoundaries`. `IDrawingContainer.GetObjects` takes a list: `GetObjects([0])`.
- Point division («Точки по кривой») gives N+1 points on an open segment, ends included. On a closed curve it gives N points from the given start.
- Line styles: `ksCSNormal` основная, `ksCSThin` тонкая, `ksCSAxial` осевая, `ksCSDashed` штриховая, `ksCSThick` утолщённая, `ksCSDash2Dots` пунктир 2.
- Point styles (`IPoint.SetStyle`): 0/2 +, 1 dot, 3 ×, 4 square, 5 triangle, **6 circle** (the hollow ○ of descriptive-geometry figures), 7 asterisk, 8 crossed square.
- Labels like 1'' come from `ks.text(x, y, s)`, where (x, y) is the bottom-left of the text. Keep labels off lines, because the text masks the line under it.
- Woven ornaments (e.g. a hexagram from stars R and R/2):
  1. Build all lines and split them at intersections.
  2. Classify faces by sampling the coloured reference figure.
  3. Keep only edges between faces of different colour.
  4. Fill each face with `fill()`.
- Short arcs in axial style (≈ 25 mm) render as one long dash, which looks like a solid line. This is normal.
- Screenshot of the real screen (for reports): `distrobox enter kompas-box -- bash -c "DISPLAY=:5 xwd -root -silent > f.xwd"; magick f.xwd f.png`. Fit the view first with `ks.doc.GetDocumentFrame().ZoomPrevNextOrAll(c.ksZoomAll)`.

## Honesty
The user may be learning from these tasks, and a teacher may ask them to redo one live. Say plainly what was estimated or might be wrong. Don't claim a drawing matches the figure until you have compared the exported PNG with it.
