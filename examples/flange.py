"""Example: a flange plate with four bolt holes and a keyed bore.

Start KOMPAS first (on Linux: kompas-nested), then:
    python3 skill/kompas-3d/scripts/run.py examples/flange.py [out_dir]     (Windows: py instead of python3)

It creates a new fragment, draws the part with final (already trimmed) geometry,
dimensions it, checks for stacked lines and saves flange.frw + flange.png to out_dir
(default: the system temp dir).
"""
import math
import os
import sys
import tempfile

import ks
from constants import constants as c

out = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else tempfile.gettempdir())
ks.new_fragment()

R = 60          # outer radius
PCD = 45        # bolt circle radius
HOLE = 6        # bolt hole radius
BORE = 20       # bore radius
KEY_W = 10      # keyway width
KEY_TOP = 24    # y of the keyway's flat top

# Outer contour, the part's centre lines and the bolt circle (also a centre line).
ks.circle(0, 0, R, with_axes=False)
h_axis, v_axis = ks.axes(0, 0, R)
ks.circle(0, 0, PCD, with_axes=False, style=c.ksCSAxial)

# Bolt holes at 45°, 135°, ... so their radial centre lines don't lie on the main axes.
centres, hole_axes = [], []
for k in range(4):
    a = math.radians(45 + 90 * k)
    x, y = PCD * math.cos(a), PCD * math.sin(a)
    centres.append((x, y))
    ks.circle(x, y, HOLE, with_axes=False)
    r1, r2 = PCD - HOLE - 3, PCD + HOLE + 3
    hole_axes.append(ks.seg(r1 * math.cos(a), r1 * math.sin(a), r2 * math.cos(a), r2 * math.sin(a), c.ksCSAxial))

# Keyed bore as one closed contour: the long arc of the bore plus three keyway sides.
y_wall = math.sqrt(BORE ** 2 - (KEY_W / 2) ** 2)          # where the keyway walls meet the bore
a_wall = math.degrees(math.atan2(y_wall, KEY_W / 2))
ks.arc(0, 0, BORE, 180 - a_wall, a_wall)                  # CCW the long way round, skipping the keyway
ks.seg(KEY_W / 2, y_wall, KEY_W / 2, KEY_TOP)
ks.seg(KEY_W / 2, KEY_TOP, -KEY_W / 2, KEY_TOP)
ks.seg(-KEY_W / 2, KEY_TOP, -KEY_W / 2, y_wall)

# Dimensions. Concentric diameters are half dimensions in free directions between the holes.
ks.ddim(0, 0, R, 160, half=True, text_at=41)                             # Ø120
ks.ddim(0, 0, PCD, 200, half=True, text_at=38)                           # Ø90, bolt circle
ks.ddim(0, 0, BORE, 250, half=True)                                      # Ø40 bore
ks.ddim(*centres[0], HOLE, 45, leader=20, prefix='4 отв. ')             # 4 holes Ø12
ks.ldim(-KEY_W / 2, KEY_TOP, KEY_W / 2, KEY_TOP, 0, KEY_TOP + 8)         # keyway width
ks.ldim(0, -BORE, KEY_W / 2, KEY_TOP, 30, 0, c.ksLinDVertical)           # bore + keyway depth
a = math.radians(-22.5)
ks.adim(hole_axes[3], h_axis, 70 * math.cos(a), 70 * math.sin(a))        # 45° to the lower right hole

problems = ks.overlaps()
print('overlaps:', problems or 'none')
ks.info()
ks.save(os.path.join(out, 'flange.frw'))
ks.export_png(os.path.join(out, 'flange.png'), dpi=200)
print('saved to', out)
