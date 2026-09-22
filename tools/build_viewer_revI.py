#!/usr/bin/env python3
"""Pack unchanged revI meshes for the interactive viewer. Millimetres throughout.
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
model = json.loads((ROOT/'design/revI.json').read_text())
layout = json.loads((ROOT/'design/layout.json').read_text())
scene = {'revision':'I', 'units':'mm', 'geometries':{}, 'parts':[], 'sources':[]}
catalog=json.loads((ROOT/'keycaps/catalog.json').read_text());cfg=catalog['default_configuration'];variants={v['id']:v for v in catalog['variants']}
scene['catalog']=catalog
scene['presets']={p.stem:json.loads(p.read_text()) for p in (ROOT/'design/configurations').glob('*.json')}
groups = {
    'tray':('Base', 'base', '#253639',0),
    'key-plate':('Plate', 'plate','#34494a',9),
    'electronics-lid':('Electronics cover','lid','#304d4e',72),
    'pcb':('PCB · unrouted outline','pcb','#22664c',3),
    'battery':('Battery · two profiles','battery','#b8c1bf',20),
    'mcu':('nice!nano · envelope','mcu','#1b433b',36),
    'display':('nice!view · envelope','display','#172c2a',52),
    'cradle':('Insulating cradle','supports','#78908a',20),
    'battery-retainer':('PCB-captured cage','supports','#78908a',24),
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
    if path.startswith('mechanical/revI/'):
        points[:,2]*=-1; ns[:,2]*=-1
    cells=vtk_to_numpy(data.GetPolys().GetData()).reshape(-1,4)
    assert np.all(cells[:,0]==3)
    # CAD (x,y,z) -> viewer (x,z,y) reflects handedness; reverse every triangle.
    indices=cells[:,[1,2,3] if path.startswith('mechanical/revI/') else [1,3,2]].reshape(-1)
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
        add(label,side,group,color,[offset,0,0],explode,mesh(f'mechanical/revI/{side}-{name}.stl'))
    for i in range(1,4):
        add(f'Washer {i}',side,'fasteners','#89918a',[offset,0,0],9,mesh(f'mechanical/revI/{side}-washer-{i}.stl'))
    for style in catalog['frame_styles']:mesh(f'mechanical/revI/{side}-frame-{style}.stl')
    for key in keys:
        choice=cfg['keycaps'][side][key['ref']];v=variants[choice['variant']]
        add('KLP '+key['ref'],side,'keycaps','#45967b' if key['row']==3 else '#e9dfc6',
            [offset+key['x'],v['seating_z_mm'],key['y']],22,mesh(v['path']),angle=key['angle']+choice['rotation_deg'])
        scene['parts'][-1]['key_ref']=key['ref']
        for label,at,size in [('Choc',9.15,[13.7,3.1,13.7]),('Stem',11.25,[9,1.3,5])]:
            add(label+' '+key['ref'],side,'switches','#253731',[offset+key['x'],at,key['y']],14,
                primitive={'kind':'box','size':size},angle=key['angle'])
    for i in range(1,6):add(f'Structural screw {i}',side,'fasteners','#56615b',[offset,0,0],9,mesh(f'mechanical/revI/{side}-screw-{i}.stl'))
    for i in range(3):
        add(f'Captive magnet {i+1}',side,'fasteners','#8c9597',[offset,0,0],0,mesh(f'mechanical/revI/{side}-magnet-{i}.stl'))
        add(f'Captive frame target {i+1}',side,'lid','#899193',[offset,0,0],72,mesh(f'mechanical/revI/{side}-frame-target-{i}.stl'))
    for i in range(2):add(f'105 mm lead storage {i+1}',side,'connectors','#ad453d' if i==0 else '#353738',[offset,0,0],24,mesh(f'mechanical/revI/{side}-battery-lead-{i}.stl'))
    for ident in catalog['battery_profiles']:mesh(f'mechanical/revI/{side}-battery-{ident}.stl')
    for i,(x,y) in enumerate([(26,26),(57,15),(28,70),(125,83)]):
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
scene['measurements']={'bay_width_mm':24,'plate_top_mm':7.6,'cover_top_mm':16.6,'themed_relief_top_mm':17.2,
                       'cover_ahead_of_top_cap_mm':round(max(0,top_key-hood_min),3),
                       'cover_ahead_of_adjacent_cap_mm':round(max(0,adjacent-hood_min),3)}
for path in ['design/revI.json','design/layout.json','tools/build_viewer_revI.py','keycaps/catalog.json']:
    scene['sources'].append({'path':path,'sha256':digest(path)})
scene['limits']=['Nominal electronic envelopes; not manufacturer CAD', 'Unrouted PCB',
                 'Nominal lead-storage paths; actual terminations, insulation and finished-pack tolerances unverified', 'PCB aperture 12.5 mm; both nominal cells fit. Magnetic force, print-in capture/temperature and physical fit need coupons',
                 'Keycap seating, switches and feet are illustrative; screw envelopes are nominal, not thread-strength proof',
                 'Exploded positions are a viewing aid, not a validated extraction path']
(ROOT/'build').mkdir(exist_ok=True)
(ROOT/'build/viewer-scene.json').write_text(json.dumps(scene,separators=(',',':'))+'\n')
print(f'Packed {len(scene["parts"])} objects, {len(scene["geometries"])} unchanged meshes; 36 keycaps.')
