#!/usr/bin/env python3
"""Intentional control vertices, analytical fillets and matching derived contours.
Run with the documented CAD Python runtime (Shapely).
SPDX-License-Identifier: GPL-3.0-or-later
"""
import json, math
from pathlib import Path
from shapely.geometry import Polygon,Point
ROOT=Path(__file__).resolve().parents[1]

def rounded(points,radius):
    corners=[]
    for i,v in enumerate(points):
        a=points[i-1];b=points[(i+1)%len(points)]
        u=[v[j]-a[j] for j in (0,1)];w=[b[j]-v[j] for j in (0,1)]
        lu=math.hypot(*u);lw=math.hypot(*w);u=[x/lu for x in u];w=[x/lw for x in w]
        turn=math.atan2(u[0]*w[1]-u[1]*w[0],sum(x*y for x,y in zip(u,w)))
        t=radius*math.tan(abs(turn)/2)
        assert t<min(lu,lw)/2,(v,'corner too short')
        start=[v[j]-u[j]*t for j in (0,1)];end=[v[j]+w[j]*t for j in (0,1)]
        sign=1 if turn>0 else -1
        center=[start[0]-u[1]*radius*sign,start[1]+u[0]*radius*sign]
        angle=math.atan2(start[1]-center[1],start[0]-center[0])
        at=lambda f:[center[0]+radius*math.cos(angle+turn*f),center[1]+radius*math.sin(angle+turn*f)]
        corners.append({'start':start,'mid':at(.5),'end':end,'samples':[at(j/16) for j in range(17)]})
    outline=[p for c in corners for p in c['samples']]
    return outline,[{'start':c['start'],'mid':c['mid'],'end':c['end']} for c in corners]

# One margin governs exposed switch faces; fasteners are deliberately not inputs.
# K32's unchanged hot-swap pad reaches 9.575 mm from its center:
# 9.575 - 7 + 1.65 PCB inset + .5 copper rule = 4.725 mm minimum.
MARGIN = 4.75

def intersect(a,b,c,d):
    u=[b[i]-a[i] for i in (0,1)];v=[d[i]-c[i] for i in (0,1)]
    w=[c[i]-a[i] for i in (0,1)]
    t=(w[0]*v[1]-w[1]*v[0])/(u[0]*v[1]-u[1]*v[0])
    return [a[i]+t*u[i] for i in (0,1)]

def control_outline(keys, margin=MARGIN):
    """Column plateaus plus offset thumb faces; bay and recess are explicit bridges."""
    d=7+margin;key={k['ref']:k for k in keys}
    top=[key['K0'+str(i)] for i in range(1,6)]
    points=[[top[0]['x']-d,top[0]['y']-d]]
    for i in range(4):
        a,b=top[i:i+2]
        x=b['x']-d if b['y']<a['y'] else a['x']+d
        points.extend([[x,a['y']-d],[x,b['y']-d]])
    points += [[top[-1]['x']+d,top[-1]['y']-d],[top[-1]['x']+d,11],
               [135,11],[135,67]]
    thumbs=[]
    for k in keys[-3:]:
        a=-math.radians(k['angle'])
        thumbs.append([[k['x']+x*math.cos(a)-y*math.sin(a),
                        k['y']+x*math.sin(a)+y*math.cos(a)]
                       for x,y in [(d,-d),(d,d),(-d,d),(-d,-d)]])
    south=[intersect(a[1],a[2],b[1],b[2]) for a,b in zip(thumbs,thumbs[1:])]
    recess=key['K22']['y']+d
    points += [thumbs[2][0],thumbs[2][1],south[1],south[0],thumbs[0][2],
               intersect(thumbs[0][2],thumbs[0][3],[0,recess],[160,recess]),
               [key['K21']['x']+d,recess],[key['K21']['x']+d,key['K21']['y']+d],
               [key['K21']['x']-d,key['K21']['y']+d]]
    return points

layout=json.loads((ROOT/'design/layout.json').read_text())
controls=control_outline(layout['halves']['left'])
outer,arcs=rounded(controls,.8);shell=Polygon(outer);assert shell.is_valid
hood,h_arcs=rounded([[111,11],[135,11],[135,67],[111,67]],1.2)
frame=Polygon(hood)
coords=lambda p:[list(v) for v in p.exterior.coords][:-1]
profiles={};frames={}
left={'outer':outer,'outer_arcs':arcs,'control_vertices':controls,'corner_radius_mm':.8,'exposed_margin_mm':MARGIN,
      'inner':coords(shell.buffer(-1.3,join_style=2)),
      'pcb_outline':coords(shell.buffer(-1.65,join_style=2).difference(Point(133,52.8).buffer(2.05,quad_segs=32))),
      'plate':coords(shell.difference(frame.buffer(.18,join_style=2))),
      'hood':hood,'hood_arcs':h_arcs}
left['pcb_cutouts']=[coords(Point(x,y).buffer(2.05,quad_segs=32)) for x,y in [(113,52.8),(122.8,64.7)]]
for side in ['left','right']:
    reflect=lambda p:[160-p[0],p[1]] if side=='right' else p
    cutouts=left.pop('pcb_cutouts',None) if side=='left' else cutouts
    profiles[side]={k:([ {n:reflect(p) for n,p in a.items()} for a in v] if k.endswith('_arcs') else [reflect(p) for p in v]) if isinstance(v,list) else v for k,v in left.items()}
    profiles[side]['pcb_cutouts']=[[reflect(p) for p in loop] for loop in cutouts]
    frames[side]={'outer':profiles[side]['hood'],'outer_arcs':profiles[side]['hood_arcs'],
                  'inner':[reflect(p) for p in coords(frame.buffer(-1.2,join_style=2))]}
    # A modest 0.4 mm lip bevel; older styles remain available as plain options.
    for style,inset in [('bevel',.4),('facet',.8)]:
        outline,arcs=rounded([[111+inset,11+inset],[135-inset,11+inset],
                             [135-inset,67-inset],[111+inset,67-inset]],1.2-inset)
        frames[side][style]=[reflect(p) for p in outline]
        frames[side][style+'_arcs']=[{n:reflect(p) for n,p in a.items()} for a in arcs]
(ROOT/'design/revI-profiles.json').write_text(json.dumps(profiles,indent=2)+'\n')
(ROOT/'design/revI-frame-profiles.json').write_text(json.dumps(frames,indent=2)+'\n')
print('22 R0.8 corners; 4.75 mm exposed rim, offset thumb faces and exact mirrored halves')
