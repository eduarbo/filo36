"""Apply viewer configurations to the open revH document; no custom proxies.
Used by the companion macro. Does not save over the user's document.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import hashlib,json,sys
from pathlib import Path
import FreeCAD as A
import Mesh
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from keycap_config import load,check

def apply(doc,config):
    catalog=load();errors,clearance=check(config,catalog)
    if errors:raise ValueError('\n'.join(errors[:12]))
    if not doc or not all(doc.getObject(p+'ActiveFrame') for p in ['L_','R_']):raise ValueError('Open mechanical/revH/Filo36.FCStd first.')
    variants={v['id']:v for v in catalog['variants']};meshes={}
    for side,keys in catalog['layout'].items():
        for key in keys:
            ident=config['keycaps'][side][key['ref']]['variant'];v=variants[ident]
            if ident not in meshes:
                path=ROOT/v['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==v['sha256'],'Modified STL: '+ident
                mesh=Mesh.Mesh(str(path));mat=A.Matrix();mat.A22=-1;mesh.transform(mat);mesh.flipNormals();meshes[ident]=mesh
    doc.openTransaction('Filo36 configuration')
    try:
        for side,prefix in [('left','L_'),('right','R_')]:
            for key in catalog['layout'][side]:
                choice=config['keycaps'][side][key['ref']];v=variants[choice['variant']];obj=doc.getObject(prefix+key['ref'])
                obj.Mesh=meshes[v['id']];obj.KeycapVariant=v['id'];obj.CapRotation=choice['rotation_deg']
                obj.Placement=A.Placement(A.Vector(key['x'],-key['y'],v['seating_z_mm']),A.Rotation(A.Vector(0,0,1),key['angle']+choice['rotation_deg']))
            f=config['frames'][side];cover=next(o for o in doc.Objects if o.Name.startswith(prefix) and hasattr(o,'FrameStyle') and o.FrameStyle==f['style'])
            doc.getObject(prefix+'ActiveFrame').setLink(cover)
            rgb=tuple(int(f['color'][i:i+2],16)/255 for i in (1,3,5));cover.ViewObject.ShapeColor=rgb
            for o in doc.Objects:
                if o.Name.startswith(prefix) and hasattr(o,'FrameStyle'):o.Visibility=False
            doc.getObject(prefix+'ActiveFrame').Visibility=True
        doc.recompute();doc.commitTransaction()
    except Exception:
        doc.abortTransaction();raise
    return clearance

def extract(doc):
    result={'schema':'filo36-config-1','revision':'H','keycaps':{},'frames':{}}
    for side,prefix in [('left','L_'),('right','R_')]:
        result['keycaps'][side]={o.KeyReference:{'variant':o.KeycapVariant,'rotation_deg':int(round(o.CapRotation.Value))%360} for o in doc.Objects if hasattr(o,'KeyReference') and o.Side==side}
        cover=doc.getObject(prefix+'ActiveFrame').LinkedObject
        color='#'+''.join(f'{round(v*255):02x}' for v in cover.ViewObject.ShapeColor[:3])
        result['frames'][side]={'style':cover.FrameStyle,'color':color}
    errors,_=check(result)
    if errors:raise ValueError('\n'.join(errors))
    return result
