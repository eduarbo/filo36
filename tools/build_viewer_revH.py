#!/usr/bin/env python3
"""Pack unchanged revH meshes for the interactive viewer. Millimetres throughout.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import base64
import hashlib
import json
from pathlib import Path
import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy

ROOT = Path(__file__).resolve().parents[1]
model = json.loads((ROOT/'design/revH.json').read_text())
layout = json.loads((ROOT/'design/layout.json').read_text())
scene = {'revision':'H', 'units':'mm', 'geometries':{}, 'parts':[], 'sources':[]}
catalog=json.loads((ROOT/'keycaps/catalog.json').read_text());cfg=catalog['default_configuration'];variants={v['id']:v for v in catalog['variants']}
scene['catalog']=catalog
scene['presets']={p.stem:json.loads(p.read_text()) for p in (ROOT/'design/configurations').glob('*.json')}
groups = {
    'tray':('Base', 'base', '#253639',0),
    'key-plate':('Plate', 'plate','#34494a',9),
    'electronics-lid':('Electronics cover','lid','#304d4e',72),
    'pcb':('PCB · unrouted outline','pcb','#22664c',3),
    'battery':('LiPo 100 mAh','battery','#b8c1bf',20),
    'mcu':('nice!nano · envelope','mcu','#1b433b',36),
    'display':('nice!view · envelope','display','#172c2a',52),
    'cradle':('Insulating cradle','supports','#78908a',20),
    'battery-retainer':('Proposed retainer','supports','#78908a',24),
    'mcu-riser':('Controller support','supports','#647d78',36),
    'display-sled':('Display support','supports','#526e67',52),
    'mcu-sockets':('Controller sockets','connectors','#273631',3),
    'jst':('Battery connector · envelope','connectors','#d9d3bc',3),
    'reset':('Reset · envelope','connectors','#545e58',3),
    'slider':('Power switch · envelope','connectors','#45514a',3),
}


def digest(path):
    return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()


def pack(array, dtype):
    return base64.b64encode(np.asarray(array,dtype=dtype).tobytes()).decode('ascii')


def mesh(path):
    if path in scene['geometries']:return path
    reader=vtk.vtkSTLReader();reader.SetFileName(str(ROOT/path));reader.Update()
    normals=vtk.vtkPolyDataNormals();normals.SetInputData(reader.GetOutput())
    normals.SetFeatureAngle(45);normals.ConsistencyOn();normals.AutoOrientNormalsOn();normals.Update()
    data=normals.GetOutput()
    points=vtk_to_numpy(data.GetPoints().GetData()).copy()[:,[0,2,1]]
    ns=vtk_to_numpy(data.GetPointData().GetNormals()).copy()[:,[0,2,1]]
    if path.startswith('mechanical/revH/'):
        points[:,2]*=-1; ns[:,2]*=-1
    cells=vtk_to_numpy(data.GetPolys().GetData()).reshape(-1,4)
    assert np.all(cells[:,0]==3)
    # CAD (x,y,z) -> viewer (x,z,y) reflects handedness; reverse every triangle.
    indices=cells[:,[1,2,3] if path.startswith('mechanical/revH/') else [1,3,2]].reshape(-1)
    scene['geometries'][path]={'positions':pack(points,'<f4'),'normals':pack(ns,'<f4'),
                             'indices':pack(indices,'<u4'),'triangles':len(cells),
                             'bounds_mm':[points.min(axis=0).tolist(),points.max(axis=0).tolist()]}
    scene['sources'].append({'path':path,'sha256':digest(path)})
    return path


def add(name,side,group,color,position,explode,geometry=None,primitive=None,angle=0):
    part={'name':side+' · '+name,'side':side,'group':group,'color':color,
          'position':position,'explode_mm':explode,'angle_deg':angle}
    if geometry:part['geometry']=geometry
    if primitive:part['primitive']=primitive
    scene['parts'].append(part)


for side,keys in layout['halves'].items():
    offset=0 if side=='left' else 161
    for name,(label,group,color,explode) in groups.items():
        add(label,side,group,color,[offset,0,0],explode,mesh(f'mechanical/revH/{side}-{name}.stl'))
    for i in range(1,6):
        add(f'Washer {i}',side,'fasteners','#89918a',[offset,0,0],9,mesh(f'mechanical/revH/{side}-washer-{i}.stl'))
    for style in catalog['frame_styles']:mesh(f'mechanical/revH/{side}-frame-{style}.stl')
    for key in keys:
        choice=cfg['keycaps'][side][key['ref']];v=variants[choice['variant']]
        add('KLP '+key['ref'],side,'keycaps','#45967b' if key['row']==3 else '#e9dfc6',
            [offset+key['x'],v['seating_z_mm'],key['y']],22,mesh(v['path']),angle=key['angle']+choice['rotation_deg'])
        scene['parts'][-1]['key_ref']=key['ref']
        for label,at,size in [('Choc',9.15,[13.7,3.1,13.7]),('Stem',11.25,[9,1.3,5])]:
            add(label+' '+key['ref'],side,'switches','#253731',[offset+key['x'],at,key['y']],14,
                primitive={'kind':'box','size':size},angle=key['angle'])
    for i,(x,y) in enumerate(model['halves'][side]['mount_holes']):
        add(f'Screw {i+1}',side,'fasteners','#202c29',[offset+x,model['halves'][side]['mount_tops_z'][i]-.12,y],
            72 if i>=3 else 9,primitive={'kind':'cylinder','radius':1.63,'height':.2})
    for i,(x,y) in enumerate([(26,26),(57,15),(41,64),(127,64)]):
        add(f'Foot {i+1}',side,'fasteners','#29352e',[offset+(x if side=='left' else 160-x),-.6,y],0,
            primitive={'kind':'cylinder','radius':3,'height':1.2})
    cx=122.8 if side=='left' else 37.2
    add('LCD · illustrative content',side,'display','#c5d1ba',[offset+cx,16.12,33.8],52,
        primitive={'kind':'screen','size':[11.3,.025,26],'text':'BASE / BLE / L' if side=='left' else 'LINK / BAT / R'})

for v in catalog['variants']:
    if v['qualified_reference_positions']:mesh(v['path'])
top_key=min(k['y']-8.244852066 for k in layout['halves']['left'] if k['row']==0)
adjacent=next(k for k in layout['halves']['left'] if k['ref']=='K05')['y']-8.244852066
hood_min=min(p[1] for p in model['halves']['left']['electronics_cover'])
scene['measurements']={'bay_width_mm':24,'plate_top_mm':7.6,'cover_top_mm':16.6,
                       'cover_ahead_of_top_cap_mm':round(max(0,top_key-hood_min),3),
                       'cover_ahead_of_adjacent_cap_mm':round(max(0,adjacent-hood_min),3)}
for path in ['design/revH.json','design/layout.json','tools/build_viewer_revH.py','keycaps/catalog.json']:
    scene['sources'].append({'path':path,'sha256':digest(path)})
scene['limits']=['Nominal electronic envelopes; not manufacturer CAD', 'Unrouted PCB',
                 'Cables, retainer fastening, contact details and physical fit pending', 'PCB battery opening: 0.15 mm cradle clearance and 0.22 mm nominal copper edge clearance; not manufacturing approved',
                 'Keycap seating, switches, screws and feet are illustrative',
                 'Exploded positions are a viewing aid, not a validated extraction path']
(ROOT/'build').mkdir(exist_ok=True)
(ROOT/'build/viewer-scene.json').write_text(json.dumps(scene,separators=(',',':'))+'\n')
print(f'Packed {len(scene["parts"])} objects, {len(scene["geometries"])} unchanged meshes; 36 keycaps.')
