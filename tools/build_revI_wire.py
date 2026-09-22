#!/usr/bin/env python3
"""A reproducible nominal storage path, not a qualified wiring harness.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import json,math
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=[[117.5,46.5],[117.5,20.1],[128,20.1],[128,26],[121,26],[121,30.5],[128,30.5],[128,35],[121,35],[121,39.5],[128,39.5],[128,44],[122.8,44],[122.8,52.8],[116,52.8],[116,55.9]]
r=1.5
length=sum(math.dist(a,b) for a,b in zip(p,p[1:]))-(len(p)-2)*r*(2-math.pi/2)
p[0][1]+=105-length
assert all(math.dist(a,b)>=2*r for a,b in zip(p,p[1:])),p
v={'units':'mm','diameter':.6,'center_z':[7.3,8.1],'minimum_bend_radius_mm':r,'centerline_length_mm':105,'control_points':p,'status':'Nominal storage for two105mm insulated leads. Wire diameter/bend radius and actual cell/connector terminations require verification; not a wiring instruction.'}
(R/'design/revI-wire-study.json').write_text(json.dumps(v,indent=2)+'\n');print('Two105mm wire storage paths; nominal0.6mm insulated diameter;R1.5 bends')
