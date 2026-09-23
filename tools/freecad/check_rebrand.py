"""Headless native readback of the metadata-only current assembly rename."""
import os,sys,json,hashlib,subprocess
from pathlib import Path
import FreeCAD as A
assert not A.GuiUp
ROOT=Path(__file__).resolve().parents[2]
report=json.loads((ROOT/'validation/rebrand-file-map.json').read_text())
entry=next(e for e in report['renames'] if e['path'].endswith('.FCStd'))
old=ROOT/'build/rebrand-original.FCStd'
old.write_bytes(subprocess.check_output(['git','show',report['baseline_commit']+':'+entry['old_path']],cwd=ROOT))
def snapshot(path):
 doc=A.openDocument(str(path));doc.recompute()
 objects={}
 for obj in doc.Objects:
  item={'type':obj.TypeId,'links':sorted(o.Name for o in obj.OutList)}
  if hasattr(obj,'Placement'):item['placement']=list(obj.Placement.toMatrix().A)
  if hasattr(obj,'Shape') and not obj.Shape.isNull():
   shape=obj.Shape;b=shape.BoundBox
   item['shape']={'valid':shape.isValid(),'volume':shape.Volume,'area':shape.Area,'bounds':[b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax],'topology':[len(shape.Solids),len(shape.Faces),len(shape.Edges),len(shape.Vertexes)]}
  if hasattr(obj,'Mesh'):item['mesh']={'points':obj.Mesh.CountPoints,'facets':obj.Mesh.CountFacets,'area':obj.Mesh.Area,'volume':obj.Mesh.Volume}
  if hasattr(obj,'ExpressionEngine'):item['expressions']=list(obj.ExpressionEngine)
  objects[obj.Name]=item
 label=doc.Label;A.closeDocument(doc.Name);return objects,label
before,_=snapshot(old);after,label=snapshot(ROOT/entry['path'])
assert before==after,'Native geometry, placements, expressions or references changed'
assert 'filo36' not in label.lower()
old.unlink()
receipt={'headless':True,'freecad_version':A.Version()[:3],'path':entry['path'],'sha256':entry['sha256'],'objects':len(after),'native_reopen_recompute':True,'geometry_placements_expressions_links_identical':True,'label':label,'baseline_commit':report['baseline_commit']}
(ROOT/'validation/rebrand-native.json').write_text(json.dumps(receipt,indent=2)+'\n')
sys.__stdout__.write('PASS: native re-open/recompute and identical geometry, placements, expressions and links\n');sys.__stdout__.flush()
if os.environ.get('FILO_FREECAD_SUBPROCESS')=='1':os._exit(0)
