"""Helpers for drawing in the active KOMPAS-3D 2D document (fragment/drawing).

All coordinates are in mm, angles in degrees. Import from a script run via run.sh:
    import ks
    ks.seg(0, 0, 100, 0); ks.save()
"""
import math, os
import ksapi
from constants import constants as c

app = ksapi.GetKompas()
if app is None:
    raise SystemExit('KOMPAS not found: it must be running and launched as the real kHome binary')
doc = app.GetActiveDocument()
d2 = ksapi.IKompasDocument2D(doc)
view = d2.GetViewsAndLayersManager().GetViews().GetActiveView()
dc = ksapi.IDrawingContainer(view)
sc = ksapi.ISymbols2DContainer(view)


def info():
    print(doc.GetName(), doc.GetFullPath(), 'type', doc.GetDocumentType(), 'changed', doc.IsChanged())
    for n in ['GetLineSegments', 'GetCircles', 'GetPoints', 'GetArcs', 'GetRegularPolygons', 'GetColourings']:
        print(' ', n[3:], getattr(dc, n)().GetCount())
    for n in ['GetLineDimensions', 'GetRadialDimensions', 'GetDiametralDimensions', 'GetAngleDimensions']:
        print(' ', n[3:], getattr(sc, n)().GetCount())


def clear():
    """Delete everything in the active view (use only on a doc you own!)."""
    for coll, getter in ((dc, 'GetColourings'), (dc, 'GetDrawingContours'), (sc, 'GetLineDimensions'),
                         (sc, 'GetRadialDimensions'), (sc, 'GetDiametralDimensions'), (sc, 'GetAngleDimensions'), (dc, 'GetLineSegments'),
                         (dc, 'GetCircles'), (dc, 'GetPoints'), (dc, 'GetArcs'), (dc, 'GetRegularPolygons')):
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
    """Centre lines (axial style) sticking out e mm beyond radius r."""
    seg(xc - r - e, yc, xc + r + e, yc, c.ksCSAxial)
    seg(xc, yc - r - e, xc, yc + r + e, c.ksCSAxial)


def circle(xc, yc, r, with_axes=True, style=c.ksCSNormal):
    ci = dc.GetCircles().Add(); ci.SetXc(xc); ci.SetYc(yc); ci.SetRadius(r); ci.SetStyle(style); ci.Update()
    if with_axes:
        axes(xc, yc, r)
    return ci


def arc(xc, yc, r, a1, a2, style=c.ksCSNormal):
    """Arc going COUNTER-CLOCKWISE from angle a1 to a2. Swap a1/a2 to get the other part of the circle."""
    ar = dc.GetArcs().Add(); ar.SetXc(xc); ar.SetYc(yc); ar.SetRadius(r)
    ar.SetAngle1(a1); ar.SetAngle2(a2); ar.SetDirection(True); ar.SetStyle(style); ar.Update()
    # Direction semantics are unreliable (True drew the clockwise complement on 2026-09-18).
    # Check the arc's midpoint (X3, Y3) against the intended CCW middle angle and flip if needed.
    am = math.radians(a1 + ((a2 - a1) % 360) / 2)
    if math.hypot(ar.GetX3() - (xc + r * math.cos(am)), ar.GetY3() - (yc + r * math.sin(am))) > r * 1e-3:
        ar.SetDirection(False); ar.Update()
    if math.hypot(ar.GetX3() - (xc + r * math.cos(am)), ar.GetY3() - (yc + r * math.sin(am))) > r * 1e-3:
        raise RuntimeError('arc midpoint still wrong: %s..%s' % (a1, a2))
    return ar


def polygon(xc, yc, r, n, angle=90, inscribed=True):
    """Regular polygon; angle=90 puts a vertex on top. inscribed=True -> vertices on circle r."""
    pg = dc.GetRegularPolygons().Add()
    pg.SetCount(n); pg.SetXc(xc); pg.SetYc(yc); pg.SetRadius(r); pg.SetAngle(angle)
    pg.SetCircumscribe(not inscribed); pg.SetStyle(c.ksCSNormal); pg.Update()
    return pg


def rdim(xc, yc, r, ang, base=None, shelf=None, under=None, shelf_dir=c.ksLSLeft):
    """Radial dimension. Course standard: DimensionType True + text on a shelf (shelf=(x, y))."""
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


def export_png(path, dpi=150, color=True):
    """Render the document to PNG. Deletes the old file first: otherwise KOMPAS pops a modal
    'file exists, replace?' dialog on the user's screen and the call hangs."""
    if os.path.exists(path):
        os.remove(path)
    p = ksapi.IRasterConvertParameters(doc.GetInterface(c.ksObjectRasterConvertParameters))
    p.SetRasterFormat(c.ksRasterFormatPNG); p.SetResolution(dpi); p.SetColorBPP(24)
    p.SetColorType(1 if color else 0)            # 0 = greyscale (default!), 1 = colour
    return doc.SaveAsToRasterFormat(path, p)


def save():
    return doc.Save()
