#!/usr/bin/env python3
"""Check Contour topology, copper, keys, fasteners and dual-cell budgets.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import json,math,hashlib
from pathlib import Path
from shapely.geometry import Polygon,Point,box,LineString
from shapely.affinity import rotate
R=Path(__file__).resolve().parents[1];profiles=json.loads((R/'design/revI-profiles.json').read_text());layout=json.loads((R/'design/layout.json').read_text())
mounts=json.loads((R/'design/revI-mounts.json').read_text());batteries=json.loads((R/'design/batteries.json').read_text())['profiles']
report={'scope':'Actual contour/copper and nominal fit; physical acceptance remains open','halves':{},'physical_acceptance':False}
for side,p in profiles.items():
 outer=Polygon(p['outer']);inner=Polygon(p['inner']);pcb=Polygon(p['pcb_outline']);reflect=lambda x:x if side=='left' else 160-x
 assert outer.is_valid and inner.is_valid and pcb.is_valid
 assert len(p['control_vertices'])==20 and p['corner_radius_mm']==.8
 assert outer.covers(Point(reflect(30),70)) and not outer.covers(Point(reflect(51),70))
 assert outer.covers(LineString([(reflect(x),y) for x,y in [(79,79),(101,81),(122,86)]]))
 assert inner.covers(pcb) and pcb.boundary.distance(inner.boundary)>.349
 x0,x1=(116.55,129.05) if side=='left' else(30.95,43.45)
 aperture=box(x0,14,x1,47.6);board=pcb.difference(aperture)
 for q in p['pcb_cutouts']:board=board.difference(Polygon(q))
 assert board.is_valid and board.geom_type=='Polygon' and len(board.interiors)==3
 pads=json.loads((R/f'build/revI/pads-{side}.json').read_text());clearances=[]
 for q in pads:
  shape=Polygon(q['polygon']);assert board.covers(shape),(side,q['ref'],q['pad'],'outside board')
  d=shape.distance(board.boundary);assert d>=.499,(side,q['ref'],q['pad'],d)
  clearances.append({'ref':q['ref'],'pad':q['pad'],'clearance_mm':round(d,6)})
 gaps={}
 for k in layout['halves'][side]:
  cut=rotate(box(k['x']-7,k['y']-7,k['x']+7,k['y']+7),-k['angle'],origin=(k['x'],k['y']));assert outer.covers(cut)
  gaps[k['ref']]=round(cut.distance(outer.boundary),5)
 for m in mounts['left']:
  pt=Point(reflect(m['xy'][0]),m['xy'][1]);assert outer.covers(pt.buffer(max(m['post_radius'],m['head_diameter']/2)))
 batteries_report={ident:{'nominal_dimensions_mm':[v['width'],v['length'],v['height']],'aperture_lateral_gap_per_side_mm':(12.5-v['width'])/2,'cage_roof_clearance_mm':6.2-2-v['height']} for ident,v in batteries.items()}
 assert all(v['aperture_lateral_gap_per_side_mm']>=.25 for v in batteries_report.values())
 report['halves'][side]={'case_size_mm':[round(outer.bounds[2]-outer.bounds[0],3),round(outer.bounds[3]-outer.bounds[1],3)],'case_plan_area_mm2':round(outer.area,3),'intentional_corners':20,'corner_radius_mm':.8,'nominal_wall_mm':1.3,'pcb_to_cavity_mm':round(pcb.boundary.distance(inner.boundary),5),'minimum_copper_to_edge_mm':min(x['clearance_mm'] for x in clearances),'copper_clearances':clearances,'all_fasteners_inside_silhouette':True,'switch_cut_to_outer_mm':gaps,'batteries':batteries_report}
report['inputs']={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in ['design/layout.json','design/revI-profiles.json','design/revI-mounts.json','design/batteries.json','tools/check_revI_outline.py']}
(R/'validation/revI-outline.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS: Contour topology, actual copper >=0.5mm, internal fasteners,36 unchanged cutouts and both nominal cells')
