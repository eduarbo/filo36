#!/usr/bin/env python3
"""Reject stale native CAD, exports or renders; verify nominal KLP plan clearance.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import hashlib,json,struct
from pathlib import Path
from shapely.geometry import Polygon,box
from shapely.affinity import rotate,translate
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def read(p):return json.loads((ROOT/p).read_text())
model=read('design/revF.json');native=read('validation/revF-native.json');render=read('validation/revF-render.json')
assert sha('mechanical/revF/Filo36.FCStd')==model['fcstd_sha256']==native['source_sha256']
for item in model['inputs']+render['meshes']:assert sha(item['path'])==item['sha256'],item['path']
for name,part in model['parts'].items():assert sha('mechanical/revF/'+name+'.stl')==part['stl_sha256'],name
for name,h in native['models'].items():assert sha('hardware/revF/models/'+name)==h,name
assert sha('design/revF.json')==render['model_sha256']
assert sha('design/layout.json')==render['layout_sha256']
assert sha('tools/render_revF.py')==render['renderer_sha256']
for name,v in render['views'].items():assert sha('docs/images/revF-'+name+'.png')==v['image_sha256']
assert '](docs/images/revF-assembled.png)' in (ROOT/'README.md').read_text()
for half in read('validation/revF-mechanical.json')['halves'].values():assert not half['collisions']
cap_bounds={}
for cap in ['normal','normal_homing','thumb']:
    data=(ROOT/('keycaps/'+cap+'.stl')).read_bytes();n=struct.unpack_from('<I',data,80)[0];points=[]
    for i in range(n):
        values=struct.unpack_from('<9f',data,96+i*50);points.extend([values[j:j+3] for j in [0,3,6]])
    cap_bounds[cap]=[min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)]
clearances={}
for side,keys in read('design/layout.json')['halves'].items():
    hood=Polygon(model['halves'][side]['electronics_cover']);polys=[]
    for k in keys:
        cap='thumb' if k['row']==3 else 'normal_homing' if k['ref']=='K14' else 'normal'
        polys.append(translate(rotate(box(*cap_bounds[cap]),-k['angle'],origin=(0,0)),k['x'],k['y']))
    gap=min(hood.distance(p) for p in polys);assert gap>=.2,(side,gap);clearances[side]=gap
print('PASS: native CAD, models, renders and meshes match; KLP plan gaps (mm):',clearances)

for path,h in read('validation/revF-stepup.json')['inputs'].items():assert sha(path)==h,path
for side,h in read('validation/revF-electrical.json')['halves'].items():assert sha('hardware/revF/filo36-'+side+'.kicad_pcb')==h['pcb_sha256']
