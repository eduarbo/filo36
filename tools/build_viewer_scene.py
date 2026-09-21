#!/usr/bin/env python3
"""Pack unchanged revE meshes for the interactive viewer. Millimetres throughout.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import base64
import hashlib
import json
from pathlib import Path
import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy
from check_artifacts import verify

ROOT = Path(__file__).resolve().parents[1]
verify()
model = json.loads((ROOT/'design/revE.json').read_text())
layout = json.loads((ROOT/'design/layout.json').read_text())
scene = {'revision':'E', 'units':'mm', 'geometries':{}, 'parts':[], 'sources':[]}
groups = {
    'tray':('Base', 'base', '#253639',0),
    'key-plate':('Plate', 'plate','#34494a',9),
    'electronics-lid':('Tapa electrónica','lid','#304d4e',72),
    'pcb':('PCB · contorno sin ruteo','pcb','#22664c',3),
    'battery':('LiPo 100 mAh','battery','#b8c1bf',20),
    'mcu':('nice!nano · envolvente','mcu','#1b433b',36),
    'display':('nice!view · envolvente','display','#172c2a',52),
    'cradle':('Cuna aislante','supports','#78908a',20),
    'mcu-riser':('Soporte del micro','supports','#647d78',36),
    'display-sled':('Soporte de pantalla','supports','#526e67',52),
    'mcu-sockets':('Sockets del micro','connectors','#273631',3),
    'jst':('Conector batería · envolvente','connectors','#d9d3bc',3),
    'reset':('Reset · envolvente','connectors','#545e58',3),
    'slider':('Interruptor · envolvente','connectors','#45514a',3),
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
    cells=vtk_to_numpy(data.GetPolys().GetData()).reshape(-1,4)
    assert np.all(cells[:,0]==3)
    # CAD (x,y,z) -> viewer (x,z,y) reflects handedness; reverse every triangle.
    indices=cells[:,[1,3,2]].reshape(-1)
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
        add(label,side,group,color,[offset,0,0],explode,mesh(f'mechanical/revE/{side}-{name}.stl'))
    for i in range(1,6):
        add(f'Arandela {i}',side,'fasteners','#89918a',[offset,0,0],9,mesh(f'mechanical/revE/{side}-washer-{i}.stl'))
    for key in keys:
        cap='thumb' if key['row']==3 else 'normal_homing' if key['ref']=='K14' else 'normal'
        add('KLP '+key['ref'],side,'keycaps','#45967b' if key['row']==3 else '#e9dfc6',
            [offset+key['x'],12.2,key['y']],22,mesh('keycaps/'+cap+'.stl'),angle=key['angle'])
        for label,at,size in [('Choc',9.15,[13.7,3.1,13.7]),('Vástago',11.25,[9,1.3,5])]:
            add(label+' '+key['ref'],side,'switches','#253731',[offset+key['x'],at,key['y']],14,
                primitive={'kind':'box','size':size},angle=key['angle'])
    for i,(x,y) in enumerate(model['halves'][side]['mount_holes']):
        add(f'Tornillo {i+1}',side,'fasteners','#202c29',[offset+x,model['halves'][side]['mount_tops_z'][i]-.12,y],
            72 if i>=3 else 9,primitive={'kind':'cylinder','radius':1.63,'height':.2})
    for i,(x,y) in enumerate([(26,26),(57,15),(41,64),(127,64)]):
        add(f'Pata {i+1}',side,'fasteners','#29352e',[offset+(x if side=='left' else 160-x),-.6,y],0,
            primitive={'kind':'cylinder','radius':3,'height':1.2})
    cx=122.8 if side=='left' else 37.2
    add('LCD · contenido ilustrativo',side,'display','#c5d1ba',[offset+cx,18.32,31.4],52,
        primitive={'kind':'screen','size':[11.3,.025,26],'text':'BASE / BLE / L' if side=='left' else 'LINK / BAT / R'})

top_key=min(k['y']-8.244852066 for k in layout['halves']['left'] if k['row']==0)
adjacent=next(k for k in layout['halves']['left'] if k['ref']=='K05')['y']-8.244852066
hood_min=min(p[1] for p in model['halves']['left']['electronics_cover'])
scene['measurements']={'bay_width_mm':24,'plate_top_mm':7.6,'cover_top_mm':19,
                       'cover_ahead_of_top_cap_mm':round(top_key-hood_min,3),
                       'cover_ahead_of_adjacent_cap_mm':round(adjacent-hood_min,3)}
for path in ['design/revE.json','design/layout.json','tools/build_viewer_scene.py']:
    scene['sources'].append({'path':path,'sha256':digest(path)})
scene['limits']=['Nominal electronic envelopes; not manufacturer CAD', 'Unrouted PCB',
                 'Cables, contact details and physical fit pending',
                 'Keycap seating, switches, screws and feet are illustrative',
                 'Exploded positions are a viewing aid, not a validated extraction path']
(ROOT/'build').mkdir(exist_ok=True)
(ROOT/'build/viewer-scene.json').write_text(json.dumps(scene,separators=(',',':'))+'\n')
print(f'Packed {len(scene["parts"])} objects, {len(scene["geometries"])} unchanged meshes; 36 keycaps.')
