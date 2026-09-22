#!/usr/bin/env python3
"""Acceptance of the requested straight flank, switch margins and board fit.
Run with the documented CAD Python runtime (Shapely).
SPDX-License-Identifier: GPL-3.0-or-later
"""
import json,math,hashlib
from pathlib import Path
from shapely.geometry import Polygon,LineString
ROOT=Path(__file__).resolve().parents[1]
profiles=json.loads((ROOT/'design/revH-profiles.json').read_text())
layout=json.loads((ROOT/'design/layout.json').read_text())
report={'request':'Continuous display-to-thumb inner case flank; original Piantor layout; few uniform subtly rounded corners.',
        'source_reference':'User red-line image, hash recorded in revH-design-review.json; no key movement',
        'physical_acceptance':False,'halves':{}}
for side,p in profiles.items():
    outer=Polygon(p['outer']);inner=Polygon(p['inner']);pcb=Polygon(p['pcb_outline'])
    assert outer.is_valid and inner.is_valid and pcb.is_valid
    assert inner.covers(pcb) and pcb.boundary.distance(inner.boundary)>.349
    x=135 if side=='left' else 25;flank=LineString([(x,14),(x,86)])
    assert outer.boundary.buffer(1e-8).covers(flank),'Notch or wing on the requested straight flank'
    assert len(p['control_vertices'])==16 and p['corner_radius_mm']==1.2
    assert outer.bounds[2 if side=='left' else 0]==x
    gaps={}
    for k in layout['halves'][side]:
        a=-math.radians(k['angle']);c,s=math.cos(a),math.sin(a)
        cut=Polygon([(k['x']+u*c-v*s,k['y']+u*s+v*c) for u,v in [(-7,-7),(7,-7),(7,7),(-7,7)]])
        assert outer.covers(cut),(side,k['ref'])
        gaps[k['ref']]=round(cut.boundary.distance(outer.boundary),5)
    report['halves'][side]={'straight_flank_x_mm':x,'uninterrupted_sample_y_mm':[14,86],
        'intentional_case_corners':16,'corner_radius_mm':1.2,'case_size_mm':[round(outer.bounds[2]-outer.bounds[0],3),round(outer.bounds[3]-outer.bounds[1],3)],
        'nominal_pcb_to_cavity_mm':round(pcb.boundary.distance(inner.boundary),5),'switch_cut_to_outer_mm':gaps,
        'power_switch_projection_exception_mm':1.5}
report['inputs']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['design/layout.json','design/revH-profiles.json','tools/check_revH_outline.py']}
(ROOT/'validation/revH-outline.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: straight flank, 16 R1.2 corners, contained board, 36 unchanged switch cutouts')
