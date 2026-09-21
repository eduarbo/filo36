# SPDX-License-Identifier: GPL-3.0-or-later
"""Read the pinned Piantor exterior; omit breakaway slots, not concavities."""
from pathlib import Path
import math
import numpy as np
import sexpdata as sexp
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union, polygonize

def source_exterior(path, tx, ty=-41):
    def tag(v): return str(v[0]) if isinstance(v,list) and v else ''
    def item(v,key): return next(x[1:] for x in v if tag(x)==key)
    lines=[]
    for v in sexp.loads(Path(path).read_text()):
        if tag(v) not in ('gr_line','gr_arc') or item(v,'layer')[0]!='Edge.Cuts': continue
        if tag(v)=='gr_line': points=[item(v,'start'),item(v,'end')]
        else:
            a,b,c=np.array([item(v,k) for k in ['start','mid','end']],float)
            center=np.linalg.solve(2*np.array([b-a,c-a]),np.array([b@b-a@a,c@c-a@a]))
            angles=[math.atan2(*(p-center)[::-1]) for p in [a,b,c]]
            ab=(angles[1]-angles[0])%(2*math.pi);ac=(angles[2]-angles[0])%(2*math.pi)
            span=ac if ab<ac else ac-2*math.pi
            radius=np.linalg.norm(a-center)
            points=[center+radius*np.array([math.cos(angles[0]+span*i/64),math.sin(angles[0]+span*i/64)]) for i in range(65)]
        lines.append(LineString([(round(x+tx,5),round(y+ty,5)) for x,y in points]))
    parts=list(polygonize(unary_union(lines)))
    assert parts, 'Source perimeter is not closed'
    exterior=Polygon(max(parts,key=lambda p:p.area).exterior)
    return exterior.buffer(.45,quad_segs=8).buffer(-.45,quad_segs=8).simplify(.045,preserve_topology=True)
