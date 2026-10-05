"""Smoke test of every helper in ks.py against a running KOMPAS (creates a scratch fragment).

    python3 skill/kompas-3d/scripts/run.py examples/selftest.py [out_dir]     (Windows: py instead of python3)

Prints OK at the end, or raises on the first failed check. Useful after a KOMPAS update.
"""
import math
import os
import sys
import tempfile

import ks
from constants import constants as c

out = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else tempfile.gettempdir())


def check(cond, what):
    if not cond:
        raise AssertionError(what)
    print('ok  ', what)


ks.new_fragment()
check(ks.doc.GetDocumentType() == c.ksDocumentFragment, 'new_fragment() creates a fragment')

# arc(): must run CCW from a1 to a2 whatever KOMPAS does with SetDirection
for a1, a2 in ((0, 90), (90, 0), (300, 60), (200, 160)):
    ar = ks.arc(0, 0, 10, a1, a2)
    am = math.radians(a1 + ((a2 - a1) % 360) / 2)
    check(math.hypot(ar.GetX3() - 10 * math.cos(am), ar.GetY3() - 10 * math.sin(am)) < 1e-3,
          f'arc {a1}..{a2} runs counter-clockwise')
ks.clear()
check(ks.dc.GetArcs().GetCount() == 0, 'clear() empties the view')

# a clean little part: square plate with a hole, polygon boss and dimensions
s = [ks.seg(0, 0, 60, 0), ks.seg(60, 0, 60, 40), ks.seg(60, 40, 0, 40), ks.seg(0, 40, 0, 0)]
hole = ks.circle(20, 20, 8)
ks.polygon(45, 20, 8, 6)
ks.rdim(20, 20, 8, 45, base=hole, shelf=(40, 45))
ks.ddim(20, 20, 8, 135, leader=10)
ks.ldim(0, 0, 60, 0, 30, -10)
ks.ldim(60, 0, 60, 40, 70, 20, c.ksLinDVertical)
ks.adim(s[3], s[0], 12, 12)           # 270° -> 0° CCW: the 90° corner
ks.fill(s, 5, 5, ks.rgb(200, 225, 255))
ks.text(0, 48, 'selftest')
check(ks.overlaps() == [], 'overlaps() reports nothing on clean geometry')

# stacked geometry must be found
ks.seg(10, 0, 30, 0)                 # lies on the bottom edge
ks.arc(20, 20, 8, 0, 90)             # lies on the hole
found = ks.overlaps()
check(len(found) == 2, f'overlaps() finds a stacked segment and arc: {found}')

frw, png = os.path.join(out, 'selftest.frw'), os.path.join(out, 'selftest.png')
ks.save(frw)
check(os.path.exists(frw), 'save(path) writes the file')
ks.export_png(png)
check(os.path.getsize(png) > 1000, 'export_png() writes a PNG')
print('OK')
