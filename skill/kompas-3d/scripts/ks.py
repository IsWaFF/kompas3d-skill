"""Helpers for drawing in a KOMPAS-3D 2D document (fragment or drawing).

Coordinates are in mm, angles in degrees, counter-clockwise from +X.
Import from a script started with run.sh:

    import ks
    ks.new_fragment()            # or keep working in the document that is already active
    ks.circle(0, 0, 50)
    print(ks.overlaps())         # [] means no stacked geometry
    ks.save('/abs/path/part.frw')
"""
import math
import os

import ksapi
from constants import constants as c

app = ksapi.GetKompas()
if app is None:
    raise SystemExit('KOMPAS not found: start it (kompas-nested), wait until it has finished loading, and make '
                     'sure it runs as the real kHome binary, not through the kompas-home-v25 symlink')

# The target document and its active view; set by use().
doc = d2 = view = dc = sc = None


def use(document):
    """Point all helpers at `document` (an IKompasDocument with a 2D view) and return it."""
    global doc, d2, view, dc, sc
    doc = document
    d2 = ksapi.IKompasDocument2D(doc)
    view = d2.GetViewsAndLayersManager().GetViews().GetActiveView()
    dc = ksapi.IDrawingContainer(view)
    sc = ksapi.ISymbols2DContainer(view)
    return doc


def new_fragment():
    """Create an empty fragment (.frw), make it active and point the helpers at it."""
    return use(app.GetDocuments().Add(c.ksDocumentFragment, True))


_active = app.GetActiveDocument()
if _active is not None and _active.GetDocumentType() in (c.ksDocumentDrawing, c.ksDocumentFragment):
    use(_active)


def info():
    print(doc.GetName(), doc.GetFullPath(), 'type', doc.GetDocumentType(), 'changed', doc.IsChanged())
    for n in ['GetLineSegments', 'GetCircles', 'GetPoints', 'GetArcs', 'GetRegularPolygons', 'GetColourings',
              'GetDrawingTexts']:
        print(' ', n[3:], getattr(dc, n)().GetCount())
    for n in ['GetLineDimensions', 'GetRadialDimensions', 'GetDiametralDimensions', 'GetAngleDimensions']:
        print(' ', n[3:], getattr(sc, n)().GetCount())


def clear():
    """Delete everything in the active view (use only on a doc you own!)."""
    for coll, getter in ((dc, 'GetColourings'), (dc, 'GetDrawingContours'), (dc, 'GetDrawingTexts'),
                         (sc, 'GetLineDimensions'), (sc, 'GetRadialDimensions'), (sc, 'GetDiametralDimensions'),
                         (sc, 'GetAngleDimensions'), (dc, 'GetLineSegments'), (dc, 'GetCircles'), (dc, 'GetPoints'),
                         (dc, 'GetArcs'), (dc, 'GetRegularPolygons')):
        col = getattr(coll, getter)()
        for i in reversed(range(col.GetCount())):
            col.GetItem(i).Delete()


def seg(x1, y1, x2, y2, style=c.ksCSNormal):
    s = dc.GetLineSegments().Add()
    s.SetX1(x1); s.SetY1(y1); s.SetX2(x2); s.SetY2(y2); s.SetStyle(style); s.Update()
    return s


def pt(x, y):
    p = dc.GetPoints().Add(); p.SetX(x); p.SetY(y); p.Update(); return p


def axes(xc, yc, r, e=5):
    """Centre lines (axial style) sticking out e mm beyond radius r. Returns (horizontal, vertical)."""
    return (seg(xc - r - e, yc, xc + r + e, yc, c.ksCSAxial),
            seg(xc, yc - r - e, xc, yc + r + e, c.ksCSAxial))


def circle(xc, yc, r, with_axes=True, style=c.ksCSNormal):
    ci = dc.GetCircles().Add(); ci.SetXc(xc); ci.SetYc(yc); ci.SetRadius(r); ci.SetStyle(style); ci.Update()
    if with_axes:
        axes(xc, yc, r)
    return ci


def arc(xc, yc, r, a1, a2, style=c.ksCSNormal):
    """Arc going COUNTER-CLOCKWISE from angle a1 to a2. Swap a1/a2 to get the other part of the circle."""
    ar = dc.GetArcs().Add(); ar.SetXc(xc); ar.SetYc(yc); ar.SetRadius(r)
    ar.SetAngle1(a1); ar.SetAngle2(a2); ar.SetDirection(True); ar.SetStyle(style); ar.Update()
    # Direction semantics are unreliable (True has drawn the clockwise complement).
    # Check the arc's midpoint (X3, Y3) against the intended CCW middle angle and flip if needed.
    am = math.radians(a1 + ((a2 - a1) % 360) / 2)
    if math.hypot(ar.GetX3() - (xc + r * math.cos(am)), ar.GetY3() - (yc + r * math.sin(am))) > r * 1e-3:
        ar.SetDirection(False); ar.Update()
    if math.hypot(ar.GetX3() - (xc + r * math.cos(am)), ar.GetY3() - (yc + r * math.sin(am))) > r * 1e-3:
        raise RuntimeError(f'arc midpoint still wrong: {a1}..{a2}')
    return ar


def polygon(xc, yc, r, n, angle=90, inscribed=True):
    """Regular polygon; angle=90 puts a vertex on top. inscribed=True -> vertices on circle r."""
    pg = dc.GetRegularPolygons().Add()
    pg.SetCount(n); pg.SetXc(xc); pg.SetYc(yc); pg.SetRadius(r); pg.SetAngle(angle)
    pg.SetCircumscribe(not inscribed); pg.SetStyle(c.ksCSNormal); pg.Update()
    return pg


def text(x, y, s, height=3.5):
    """One line of text; (x, y) is its bottom-left corner. Keep it off lines: text masks what is under it."""
    t = dc.GetDrawingTexts().Add()
    t.SetX(x); t.SetY(y)
    item = ksapi.IText(t).Add().Add()
    item.SetStr(s); ksapi.ITextFont(item).SetHeight(height)
    t.Update()
    return t


def rdim(xc, yc, r, ang, base=None, shelf=None, under=None, shelf_dir=c.ksLSLeft):
    """Radial dimension, half style (DimensionType True). shelf=(x, y) puts the text on a shelf there,
    which is what many engineering-graphics courses want. under: text under the value, e.g. '3 отв.'."""
    rd = sc.GetRadialDimensions().Add()
    rd.SetXc(xc); rd.SetYc(yc); rd.SetRadius(r); rd.SetAngle(ang)
    rd.SetDimensionType(True)
    if shelf:
        pr = ksapi.IDimensionParams(rd)
        pr.SetTextOnLine(c.ksDTPOnShelf); pr.SetShelfDirection(shelf_dir)
        rd.SetShelfX(shelf[0]); rd.SetShelfY(shelf[1])
    if base is not None:
        rd.SetBaseObject(base)
    if under:
        ksapi.IDimensionText(rd).GetTextUnder().SetStr(under)   # e.g. '3 отв.'
    rd.Update()
    return rd


def ddim(xc, yc, r, ang, half=False, text_at=None, leader=None, shelf_dir=None, prefix=None, base=None):
    """Diametral dimension (Ø) with the dimension line at `ang` degrees through the centre.
    half=True: one arrow, line broken just past the centre (usual for concentric circles
    with a crowded centre). The text masks lines under it, so keep it off contours:
    text_at=mm moves it along the dimension line (measured from the line's far end, past the centre).
    Small circles get their text on a leader + shelf automatically: leader=mm pushes the text
    further out (KOMPAS scales it a bit), shelf_dir=c.ksLSRight / c.ksLSLeft picks the shelf side.
    prefix: text before the value, e.g. '4 отв. '."""
    dd = sc.GetDiametralDimensions().Add()
    dd.SetXc(xc); dd.SetYc(yc); dd.SetRadius(r); dd.SetAngle(ang)
    dd.SetDimensionType(half)
    if text_at is not None:
        pr = ksapi.IDimensionParams(dd)
        pr.SetTextType(c.ksDimTManual); pr.SetTextPos(text_at)
    elif leader is not None or shelf_dir is not None:
        pr = ksapi.IDimensionParams(dd)
        pr.SetTextOnLine(c.ksDTPOnShelf)
        if leader is not None:
            pr.SetTextPos(leader)
        if shelf_dir is not None:
            pr.SetShelfDirection(shelf_dir)
    if base is not None:
        dd.SetBaseObject(base)
    if prefix:
        ksapi.IDimensionText(dd).GetPrefix().SetStr(prefix)
    dd.Update()
    return dd


def ldim(x1, y1, x2, y2, x3, y3, orient=c.ksLinDHorizontal, sign=None):
    """Linear dimension between (x1,y1)-(x2,y2), dimension line through (x3,y3).
    orient: ksLinDHorizontal / ksLinDVertical / ksLinDParallel. sign=2 -> square symbol."""
    ld = sc.GetLineDimensions().Add()
    ld.SetX1(x1); ld.SetY1(y1); ld.SetX2(x2); ld.SetY2(y2); ld.SetX3(x3); ld.SetY3(y3)
    ld.SetOrientation(orient)
    if sign is not None:
        ksapi.IDimensionText(ld).SetSign(sign)
    ld.Update()
    return ld


def adim(line1, line2, x, y):
    """Angle dimension between two segments (as returned by seg()/axes()); they need not touch.
    KOMPAS measures COUNTER-CLOCKWISE from line1's direction to line2's (direction = the segment's
    start -> end), so swap the arguments if you get the reflex angle. (x, y) sets where the
    dimension arc and text go. Binding to objects is the only reliable way: with bare
    X1/Y1/X2/Y2 points, KOMPAS measures the second ray from the sheet origin, not the vertex."""
    ad = sc.GetAngleDimensions().Add(c.ksDrADimension)
    ad.SetBaseObject1(line1); ad.SetBaseObject2(line2)
    ad.SetX3(x); ad.SetY3(y)
    ad.Update()
    return ad


def rgb(r, g, b):
    """KOMPAS colours are COLORREF (0xBBGGRR)."""
    return r | (g << 8) | (b << 16)


def fill(objects, x, y, color):
    """Solid colour fill of the closed region around point (x, y) bounded by `objects`."""
    grp = dc.GetDrawingContours().MakeEncloseContours(objects, x, y, False)
    col = dc.GetColourings().Add()
    col.SetColouringType(c.ksColouringSolid); col.SetColor1(color)
    ksapi.IBoundariesObject(col).AddBoundaries(grp.GetObjects([0]), True)
    col.Update()
    return col


def _items(collection, iface):
    """All items of a collection, cast to `iface` (GetItem returns a bare IDrawingObject)."""
    return [iface(collection.GetItem(i)) for i in range(collection.GetCount())]


def overlaps(tol=1e-3):
    """Find stacked geometry in the active view: collinear segments that overlap, and arcs/circles
    lying on the same circle with overlapping angular ranges (style is ignored: an axial line on
    top of a contour line counts too). Returns readable strings; an empty list means clean."""
    found = []
    segs = [(s.GetX1(), s.GetY1(), s.GetX2(), s.GetY2()) for s in _items(dc.GetLineSegments(), ksapi.ILineSegment)]
    for i, (ax, ay, bx, by) in enumerate(segs):
        length = math.hypot(bx - ax, by - ay)
        if length < tol:
            continue
        ux, uy = (bx - ax) / length, (by - ay) / length
        for j in range(i + 1, len(segs)):
            cx, cy, ex, ey = segs[j]
            # both ends of segment j must lie on the line of segment i
            if abs((cx - ax) * uy - (cy - ay) * ux) > tol or abs((ex - ax) * uy - (ey - ay) * ux) > tol:
                continue
            t1, t2 = sorted(((cx - ax) * ux + (cy - ay) * uy, (ex - ax) * ux + (ey - ay) * uy))
            common = min(length, t2) - max(0.0, t1)
            if common > tol:
                found.append(f'segments #{i} and #{j} overlap by {common:.2f} mm')

    # every circle-like object as (name, xc, yc, r, start angle, CCW sweep)
    rings = [(f'circle #{i}', ci.GetXc(), ci.GetYc(), ci.GetRadius(), 0.0, 360.0)
             for i, ci in enumerate(_items(dc.GetCircles(), ksapi.ICircle))]
    for i, ar in enumerate(_items(dc.GetArcs(), ksapi.IArc)):
        xc, yc = ar.GetXc(), ar.GetYc()
        a1, a2, a3 = (math.degrees(math.atan2(y - yc, x - xc)) for x, y in
                      ((ar.GetX1(), ar.GetY1()), (ar.GetX2(), ar.GetY2()), (ar.GetX3(), ar.GetY3())))
        # Angle1/Angle2/Direction can't be trusted; the midpoint says which way the arc runs
        start, end = (a1, a2) if (a3 - a1) % 360 < (a2 - a1) % 360 else (a2, a1)
        rings.append((f'arc #{i}', xc, yc, ar.GetRadius(), start, (end - start) % 360))
    eps = 1e-3
    for i, (n1, x1, y1, r1, s1, w1) in enumerate(rings):
        for n2, x2, y2, r2, s2, w2 in rings[i + 1:]:
            if math.hypot(x1 - x2, y1 - y2) > tol or abs(r1 - r2) > tol:
                continue
            if (s2 - s1) % 360 < w1 - eps or (s1 - s2) % 360 < w2 - eps:
                found.append(f'{n1} and {n2} lie on the same circle R{round(r1, 3):g} and overlap')
    return found


def export_png(path, dpi=150, color=True):
    """Render the document to PNG. Deletes the old file first: otherwise KOMPAS pops a modal
    'file exists, replace?' dialog on the user's screen and the call hangs."""
    if os.path.exists(path):
        os.remove(path)
    p = ksapi.IRasterConvertParameters(doc.GetInterface(c.ksObjectRasterConvertParameters))
    p.SetRasterFormat(c.ksRasterFormatPNG); p.SetResolution(dpi); p.SetColorBPP(24)
    p.SetColorType(1 if color else 0)            # 0 = greyscale (default!), 1 = colour
    return doc.SaveAsToRasterFormat(path, p)


def save(path=None):
    """Save the document. A new document has no file yet: pass an absolute path,
    otherwise KOMPAS opens a modal 'Save as' dialog and the script hangs."""
    return doc.SaveAs(path) if path else doc.Save()
