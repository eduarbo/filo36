#!/usr/bin/env python3
"""Conservative swept KLP mesh/head clearance for every qualified reference choice.
Actual STL triangles clipped to the screw-height travel slab, then a convex XY bound.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import json,struct,hashlib,math
from pathlib import Path
import numpy as np
from shapely.geometry import MultiPoint,Point
from shapely.affinity import rotate,translate
R=Path(__file__).resolve().parents[1]
c=json.loads((R/'keycaps/catalog.json').read_text());mounts=json.loads((R/'design/revI-mounts.json').read_text())['left']
minimum=1000.;count=0;limiting=None
for v in c['variants']:
 if not v['qualified_reference_positions']:continue
 raw=(R/v['path']).read_bytes();n=struct.unpack_from('<I',raw,80)[0]
 triangles=np.ndarray((n,),dtype=np.dtype([('n','<f4',(3,)),('v','<f4',(3,3)),('a','<u2')]),buffer=raw,offset=84)['v']
 for m in mounts:
  zmax=m['seat_z']+m['head_height']+c['study_travel_mm']-v['seating_z_mm'];vertices=[]
  for tri in triangles[triangles[:,:,2].min(axis=1)<=zmax]:
   poly=[]
   for a,b in zip(tri,np.roll(tri,-1,axis=0)):
    if a[2]<=zmax:poly.append(a)
    if (a[2]<zmax<b[2]) or (b[2]<zmax<a[2]):poly.append(a+(b-a)*((zmax-a[2])/(b[2]-a[2])))
   vertices.extend(p[:2] for p in poly)
  if not vertices:continue
  hull=MultiPoint(vertices).convex_hull
  for choice in v['qualified_reference_positions']:
   key=next(k for k in c['layout'][choice['side']] if k['ref']==choice['key'])
   shape=translate(rotate(hull,-key['angle']-choice['rotation_deg'],origin=(0,0)),xoff=key['x'],yoff=key['y'])
   x,y=m['xy'];x=x if choice['side']=='left' else 160-x
   gap=shape.distance(Point(x,y))-m['head_diameter']/2
   assert gap>0,(v['id'],choice,m['id'],gap)
   if gap<minimum:minimum=gap;limiting={'variant':v['id'],'choice':choice,'mount':m['id']}
   count+=1
report={'scope':'Conservative full 3.5 mm vertical KLP travel versus actual nominal screw heads; physical seating remains untested','checked_reference_choice_head_pairs':count,'minimum_xy_clearance_mm':minimum,'limiting':limiting,'inputs':{f:hashlib.sha256((R/f).read_bytes()).hexdigest() for f in ['keycaps/catalog.json','design/revI-mounts.json','tools/check_revI_fasteners.py']},'physical_acceptance':False}
(R/'validation/revI-fasteners.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS:',count,'qualified KLP/head sweeps; minimum XY clearance',minimum)
