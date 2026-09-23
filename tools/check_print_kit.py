#!/usr/bin/env python3
"""Verify browser print selections, native bytes and 3MF oriented surfaces.
SPDX-License-Identifier: GPL-3.0-or-later
"""
from pathlib import Path
import json,zipfile,hashlib,struct,xml.etree.ElementTree as E
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/themes-print'
def triangles_stl(raw):
 n=struct.unpack_from('<I',raw,80)[0];assert len(raw)==84+50*n
 return np.stack([np.array(struct.unpack_from('<9f',raw,84+i*50+12)).reshape(3,3) for i in range(n)])
def canonical(triangles):
 # Allow cyclic starts, but never reversed winding.
 result=[]
 for t in triangles:
  p=[tuple(round(float(v),5) for v in row) for row in t];result.append(min(tuple(p[i:]+p[:i]) for i in range(3)))
 return sorted(result)
def topo(t):
 vertices={};faces=[]
 for tri in t:
  ids=[]
  for p in tri:
   key=tuple(round(float(v),5) for v in p)
   if key not in vertices:vertices[key]=len(vertices)
   ids.append(vertices[key])
  faces.append(ids)
 from collections import Counter
 edges=Counter(tuple(sorted((ids[i],ids[(i+1)%3]))) for ids in faces for i in range(3))
 return {'vertices':len(vertices),'edges':len(edges),'open_or_nonmanifold_edges':sum(v!=2 for v in edges.values()),'signed_volume_mm3':float(np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()/6)}
results=[]
for filename,expected in [('complete.zip',19),('left-shells.zip',3)]:
 z=zipfile.ZipFile(OUT/filename);manifest=json.loads(z.read('manifest.json'));config=json.loads(z.read('Flan36-config.json'));assert config==manifest['configuration'];assert len(manifest['parts'])==expected
 assert all(p['side']=='left' for p in manifest['parts']) if filename.startswith('left') else True
 assert not any('right-frame' in p['id'] for p in manifest['parts'])
 assert sum('washer' in p['id'] for p in manifest['parts'])==(6 if filename=='complete.zip' else 0)
 records=[]
 for p in manifest['parts']:
  raw=z.read('STL/'+p['id']+'.stl');source=(ROOT/p['source']).read_bytes();assert raw==source;assert hashlib.sha256(raw).hexdigest()==p['source_sha256'];actual=triangles_stl(raw)
  import io
  colored=zipfile.ZipFile(io.BytesIO(z.read('3MF/'+p['id']+'.3mf')));rt=E.fromstring(colored.read('3D/3dmodel.model'));assert rt.attrib['unit']=='millimeter'
  pts=np.array([[float(v.attrib[a]) for a in ['x','y','z']] for v in rt.iter() if v.tag.endswith('}vertex')]);ids=np.array([[int(v.attrib[a]) for a in ['v1','v2','v3']] for v in rt.iter() if v.tag.endswith('}triangle')]);restored=pts[ids]-np.array(p['translation_3mf_mm']);assert np.max(np.abs(restored-actual))<1e-5
  assert canonical(actual)==canonical(restored);a,b=topo(actual),topo(restored);assert a['open_or_nonmanifold_edges']==b['open_or_nonmanifold_edges']==0,(p['id'],a,b);assert abs(a['signed_volume_mm3']-b['signed_volume_mm3'])<.001
  faces=[v for v in rt.iter() if v.tag.endswith('}triangle')]
  from collections import Counter
  counts=Counter(int(t.attrib['p1']) for t in faces)
  for i,role in enumerate(p['role_triangles']):assert counts[i]==role['count']
  assert all(t.attrib['pid']=='1' and t.attrib['paint_color']==['4','8','0C','1C'][int(t.attrib['p1'])] for t in faces)
  assert 'Metadata/project_settings.config' not in colored.namelist()
  palette=[v.attrib['color'][:7].lower() for v in rt.iter() if v.tag.endswith('}color')];assert palette==[p['colors'].get(k,p['colors']['body']) for k in ['body','detail','accent','secondary']]
  records.append({'id':p['id'],'stl_bytes_identical':True,'oriented_surface_preserved':True,'closed':True,'triangles':len(actual),'colors':palette})
 results.append({'file':filename,'parts':records,'eye_solo_explosion_do_not_remove_printables':True})
report={'passed':True,'kits':results,'slicer_palette_automatic_import':'not accepted; explicit manual mapping required','no_manufacturing_acceptance':True};(OUT/'print-validation.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS: exact native STLs, selected installed parts, washers, closed oriented 3MF surfaces and color mappings')
