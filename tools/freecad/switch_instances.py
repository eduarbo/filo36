"""Add inspectable linked KiSwitch meshes without changing mechanical solids.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import json
from pathlib import Path
import FreeCAD as A,Mesh
ROOT=Path(__file__).resolve().parents[2]
def ensure(doc):
 if doc.getObject('ChocV1Source'):return False
 prototype=doc.addObject('App::Part','ChocV1Source');prototype.Label='Choc v1 · KiSwitch source (MIT)'
 data=json.loads((ROOT/'components/switches.json').read_text())
 for entries in [data['choc-body'],data['choc-stem']]:
  for entry in entries:
   o=doc.addObject('Mesh::Feature','ChocSource');o.Label=entry['name'];o.Mesh=Mesh.Mesh(str(ROOT/entry['path']));o.ViewObject.ShapeColor=tuple(int(entry['color'][i:i+2],16)/255 for i in (1,3,5));prototype.addObject(o)
 for side,keys in json.loads((ROOT/'design/layout.json').read_text())['halves'].items():
  prefix='L_' if side=='left' else 'R_';half=doc.getObject(prefix+'Half');group=doc.addObject('App::Part',prefix+'Switches');group.Label='Choc v1 · visual references';half.addObject(group)
  for key in keys:
   link=doc.addObject('App::Link',prefix+'Switch_'+key['ref']);link.setLink(prototype);link.LinkPlacement=A.Placement(A.Vector(key['x'],-key['y'],5.4),A.Rotation(A.Vector(0,0,1),key['angle']));link.Label=key['ref']+' · Choc v1';group.addObject(link)
 prototype.Visibility=False;doc.recompute();return True
