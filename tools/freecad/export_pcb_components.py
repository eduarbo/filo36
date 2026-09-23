"""Synchronize revI's existing relative STEP references with the native models.
PCB footprints, nets, model references and historical revisions are never written.
SPDX-License-Identifier: GPL-3.0-or-later
"""
from pathlib import Path
import hashlib,json,re,os,sys
import FreeCAD as A,FreeCADGui as G,Part
G.showMainWindow()
import ImportGui
R=Path(__file__).resolve().parents[2];source=R/'mechanical/revI/Filo36.FCStd';digest=hashlib.sha256(source.read_bytes()).hexdigest()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def children(text):
 depth=0;quoted=False;escaped=False;start=None
 for i,c in enumerate(text):
  if quoted:
   if escaped:escaped=False
   elif c=='\\':escaped=True
   elif c=='"':quoted=False
  elif c=='"':quoted=True
  elif c=='(':
   depth+=1
   if depth==2:start=i
  elif c==')':
   if depth==2:yield text[start:i+1]
   depth-=1
native=A.openDocument(str(source));parts={o.PartID:o for o in native.Objects if hasattr(o,'PartID')};out=R/'hardware/revI/models';report={'source_sha256':digest,'checker_sha256':sha(Path(__file__)),'models':{},'pcb_unchanged':{},'scope':'STEP import readback and reconstruction at actual footprint datums; nominal geometry, not physical fit or routing acceptance.'}
def difference(a,b):
 # Match constituent solids before exact Booleans. This checks each solid,
 # including overlapping pad/body regions, without a quadratic compound Boolean.
 remaining=list(b.Solids);assert len(a.Solids)==len(remaining)
 def bounds(s):
  # GUI tessellation can underbound circular pads; compare analytic bounds.
  b=s.cleaned().BoundBox
  return [getattr(b,k) for k in ['XMin','YMin','ZMin','XMax','YMax','ZMax']]
 total=0
 for first in a.Solids:
  box=bounds(first);dist=lambda second:max(abs(x-y) for x,y in zip(box,bounds(second)))
  index=min(range(len(remaining)),key=lambda i:dist(remaining[i]));second=remaining.pop(index);assert dist(second)<1e-5, (box,bounds(second),dist(second))
  total+=first.cut(second,1e-6).Volume+second.cut(first,1e-6).Volume
 return total
def export(name,shape,colors,pose=None,reference=None):
 # Preserve analytic geometry and place the transform on constituent solids.
 # The STEP exporter can reset a single top-level object's placement.
 shape=Part.makeCompound(shape.Solids)
 tmp=A.newDocument('ModelExport');obj=tmp.addObject('Part::Feature','Component');obj.Label=name;obj.Shape=shape;obj.ViewObject.DiffuseColor=colors;tmp.recompute();p=out/(name+'.step');ImportGui.export([obj],str(p));A.closeDocument(tmp.Name)
 loaded=A.newDocument('ModelReadback');ImportGui.insert(str(p),loaded.Name);loaded.recompute();items=[o for o in loaded.Objects if o.TypeId=='Part::Feature' and not o.Shape.isNull()];leaves=[]
 for item in items:
  leaf=item.Shape.copy();leaf.Placement=item.getGlobalPlacement();leaves.append(leaf)
 read=Part.makeCompound(leaves)
 diff=difference(shape,read);assert diff<.001,(name,'STEP surface readback',diff)
 distinct=len(set(tuple(round(v,3) for v in c[:3]) for item in items for c in item.ViewObject.DiffuseColor));expected=len(set(tuple(round(v,3) for v in c[:3]) for c in colors));assert distinct==expected,(name,'STEP colors',distinct,expected)
 def colored_area(sh,col):
  if len(col)==1:col=list(col)*len(sh.Faces)
  assert len(sh.Faces)==len(col)
  areas={}
  for f,c in zip(sh.Faces,col):
   key=tuple(round(v,3) for v in c[:3]);areas[key]=areas.get(key,0)+f.Area
  return areas
 wanted=colored_area(shape,colors);actual={}
 for item in items:
  for key,area in colored_area(item.Shape,item.ViewObject.DiffuseColor).items():actual[key]=actual.get(key,0)+area
 assert actual.keys()==wanted.keys()
 area_error=max(abs(wanted[k]-actual[k]) for k in wanted)
 assert area_error<1e-4,(name,'STEP face material area',area_error)
 if pose:
  read.rotate(A.Vector(),A.Vector(0,0,1),pose[2]);read.translate(A.Vector(pose[0],-pose[1],5.4));placed=difference(read,reference);assert placed<.001,(name,'footprint registration',placed)
 else:placed=0
 report['models'][name]={'path':str(p.relative_to(R)),'sha256':sha(p),'import_difference_mm3':diff,'native_placement_difference_mm3':placed,'distinct_colors':distinct,'color_area_error_mm2':area_error,'footprint_pose_xy_deg':pose}
 A.closeDocument(loaded.Name);sys.__stdout__.write(name+' verified\n');sys.__stdout__.flush()
for side in ['left','right']:
 pcb=R/f'hardware/revI/filo36-{side}.kicad_pcb';before=sha(pcb);footprints={}
 for block in children(pcb.read_text()):
  if not block.startswith('(footprint '):continue
  ref=re.search(r'\(property\s+"Reference"\s+"([^\"]+)"',block)[1];at=re.search(r'\(at\s+([\d.eE+-]+)\s+([\d.eE+-]+)(?:\s+([\d.eE+-]+))?\)',block);footprints[ref]=(block,[float(at[1]),float(at[2]),float(at[3] or 0)])
 for ref,part in {'U1':'mcu','J2':'display','J1':'jst','SW1':'slider','SW2':'reset'}.items():
  block,pose=footprints[ref];name=side+'-'+part;assert '${KIPRJMOD}/models/'+name+'.step' in block
  for field,expected in [('offset',[0,0,0]),('rotate',[0,0,0]),('scale',[1,1,1])]:
   val=re.search(r'\('+field+r'\s*\(xyz\s+([^)]*)\)',block);assert [float(v) for v in val[1].split()]==expected
  obj=parts[name];shape=obj.Shape.copy();shape.translate(A.Vector(-pose[0],pose[1],-5.4));shape.rotate(A.Vector(),A.Vector(0,0,1),-pose[2]);colors=list(obj.ViewObject.DiffuseColor);colors=colors if len(colors)==len(shape.Faces) else [obj.ViewObject.ShapeColor]*len(shape.Faces)
  export(name,shape,colors,pose,obj.Shape)
 assert sha(pcb)==before;report['pcb_unchanged'][side]=before
A.closeDocument(native.Name)
# Keep the historical relative filename so no footprint/model-link edits are needed.
switch=A.openDocument(str(R/'components/sources/SW_Kailh_Choc_V1.FCStd'));shapes=[];colors=[]
palette={'Upper_Housing':(.816,.827,.796),'Lower_Housing':(.141,.153,.161),'Pin_1':(.725,.624,.384),'Pin_2':(.725,.624,.384),'Stem':(.729,.251,.278)}
for obj in switch.Objects:
 if obj.Label in palette:
  shape=obj.Shape.copy();shape.Placement=obj.getGlobalPlacement();shapes.append(shape);colors.extend([palette[obj.Label]]*len(shape.Faces))
export('choc-envelope',Part.makeCompound(shapes),colors);A.closeDocument(switch.Name)
assert sha(source)==digest
(R/'validation/revI-pcb-component-models.json').write_text(json.dumps(report,indent=2)+'\n')
sys.__stdout__.write('PASS: 11 relative colored STEP models match nominal source; both PCB files unchanged\n');sys.__stdout__.flush()
if os.environ.get('FILO_FREECAD_SUBPROCESS')=='1':os._exit(0)
