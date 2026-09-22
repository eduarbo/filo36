#!/usr/bin/env python3
"""Read-only provenance, key-layout and exact mesh-vertex check for the 3D viewer.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import gzip
import base64
import hashlib
import json
import re
from pathlib import Path
import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy

ROOT=Path(__file__).resolve().parents[1]
html=(ROOT/'docs/index.html').read_bytes()
receipt=json.loads((ROOT/'validation/revI-viewer.json').read_text())
assert hashlib.sha256(html).hexdigest()==receipt['viewer_sha256']
for source in receipt['sources']:
    assert hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest()==source['sha256'],source['path']
data=json.loads(gzip.decompress(base64.b64decode(re.search(rb'<script id="scene-data" type="application/octet-stream">(.*?)</script>',html,re.S)[1])))
assert len(data['parts'])==180
for side,expected_x in [('left',117.05),('right',31.45)]:
    bounds=data['geometries'][f'mechanical/revI/{side}-battery.stl']['bounds_mm']
    assert abs(bounds[0][0]-expected_x)<1e-4 and abs(bounds[0][1]-2)<1e-5,(side,'unplaced battery')
layout=json.loads((ROOT/'design/layout.json').read_text())
caps=[p for p in data['parts'] if p['group']=='keycaps'];assert len(caps)==36
for side,keys in layout['halves'].items():
    for k in keys:
        p=next(p for p in caps if p['name']==side+' · KLP '+k['ref'])
        assert p['position']==[(161 if side=='right' else 0)+k['x'],12.2,k['y']]
        assert p['angle_deg']==k['angle']
model=json.loads((ROOT/'design/revI.json').read_text())
switches=json.loads((ROOT/'components/switches.json').read_text())
decode=lambda g,k,dtype:np.frombuffer(base64.b64decode(g[k]),dtype=dtype)
for path,g in data['geometries'].items():
    if path.endswith('#materials'):
        part=next(p for p in data['parts'] if p.get('geometry')==path)
        parent=path.removesuffix('#materials')
        visuals=switches[parent] if parent in switches else model['parts'][Path(parent).stem]['visuals']
        assert part['materials']==[v['color'] for v in visuals]
        assert len(part['materials'])==len(g['groups'])
        ps=[];ns=[];ix=[];vertex=0;offset=0
        for i,v in enumerate(visuals):
            child=data['geometries'][v['path']];p=decode(child,'positions','<f4');n=decode(child,'normals','<f4');indices=decode(child,'indices','<u4')
            ps.append(p);ns.append(n);ix.append(indices+vertex)
            assert g['groups'][i]=={'start':offset,'count':len(indices),'materialIndex':i}
            vertex+=len(p)//3;offset+=len(indices)
        assert np.array_equal(decode(g,'positions','<f4'),np.concatenate(ps)),path
        assert np.array_equal(decode(g,'normals','<f4'),np.concatenate(ns)),path
        assert np.array_equal(decode(g,'indices','<u4'),np.concatenate(ix)),path
        assert offset==g['triangles']*3
        continue
    reader=vtk.vtkSTLReader();reader.SetFileName(str(ROOT/path));reader.Update();mesh=reader.GetOutput()
    expected=vtk_to_numpy(mesh.GetPoints().GetData()).copy()[:,[0,2,1]]
    if path.startswith('mechanical/revI/'):expected[:,2]*=-1
    actual=np.frombuffer(base64.b64decode(g['positions']),dtype='<f4').reshape(-1,3)
    assert set(map(tuple,actual))==set(map(tuple,expected)),path
    assert g['triangles']==mesh.GetNumberOfCells(),path
print(f'PASS: viewer and sources match; 36 key positions/angles; {len(data["geometries"])} meshes preserve vertices and triangle counts.')
