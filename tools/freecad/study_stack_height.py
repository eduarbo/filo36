"""Explore nominal display/cover heights without saving the native source.
Run with the documented FreeCAD runtime. Only left-half affected pairs are
checked; connector datums, tolerances, release paths and physical fit are open.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import FreeCAD as A,FreeCADGui as G,Part,json,os,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];G.showMainWindow();doc=A.openDocument(str(ROOT/'mechanical/revI/Filo36.FCStd'))
def log(*x):sys.__stdout__.write(' '.join(map(str,x))+'\n');sys.__stdout__.flush()
for p in ['L_','R_']:doc.getObject(p+'Half').Placement=A.Placement()
doc.recompute()
report={'source_sha256':hashlib.sha256((ROOT/'mechanical/revI/Filo36.FCStd').read_bytes()).hexdigest(),'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'Read-only left-half affected-pair nominal height study; no source save, contact qualification, tolerance or release-path acceptance','current':{},'candidates':{}}
for k in ['left-mcu','left-display','left-battery','left-jst','left-display-sled','left-electronics-lid']:
 o=next(o for o in doc.Objects if getattr(o,'PartID',None)==k);b=o.Shape.BoundBox;report['current'][k]={'zmin':b.ZMin,'zmax':b.ZMax}
for db,top in [(12.4,14.8),(12.4,15.6)]:
 doc.Parameters.set(doc.Parameters.getCellFromAlias('DisplayBottom'),str(db)+' mm')
 doc.Parameters.set(doc.Parameters.getCellFromAlias('FrameTop'),str(top)+' mm');doc.recompute()
 # Assert aliases to prevent worksheet index mistakes.
 assert abs(doc.Parameters.DisplayBottom.Value-db)<1e-6,(doc.Parameters.DisplayBottom,db)
 assert abs(doc.Parameters.FrameTop.Value-top)<1e-6
 shapes={o.PartID[5:]:o.Shape for o in doc.Objects if getattr(o,'PartID','').startswith('left-')}
 frames=[o for o in doc.Objects if hasattr(o,'FrameStyle') and o.TypeId!='App::Link' and o.Name.startswith('L_')]
 hits={}
 changed={'display','display-sled','electronics-lid'}
 for n in changed:
  for k,s in shapes.items():
   if n==k or not shapes[n].BoundBox.intersect(s.BoundBox):continue
   v=shapes[n].common(s).Volume
   if v>.001:hits[n+' / '+k]=round(v,6)
 for frame in frames:
  for k,s in shapes.items():
   if k=='electronics-lid' or not frame.Shape.BoundBox.intersect(s.BoundBox):continue
   v=frame.Shape.common(s).Volume
   if v>.001:hits[frame.FrameStyle+' / '+k]=round(v,6)
 report['candidates'][str(top)]={'display_bottom':db,'frame_top':top,'raised_relief_top':top+.6,'collisions_mm3':hits,'mcu_display_distance_mm':shapes['mcu'].distToShape(shapes['display'])[0],'battery_connector_roof_gap_mm':top-doc.Parameters.FrameRoof.Value-shapes['jst'].BoundBox.ZMax}
 log(top,hits)
assert hashlib.sha256((ROOT/'mechanical/revI/Filo36.FCStd').read_bytes()).hexdigest()==report['source_sha256']
report['native_source_unchanged']=True
(ROOT/'validation/revI-stack-study.json').write_text(json.dumps(report,indent=2)+'\n');log(report);os._exit(0)
