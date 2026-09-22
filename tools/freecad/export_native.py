"""Export the active revF FCStd, preserving manual changes in the source document.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import hashlib
import json
from pathlib import Path
import FreeCAD as A
import Part
import MeshPart

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'mechanical/revF'
doc=A.ActiveDocument
if not doc or not doc.getObject('Parameters'):
    raise RuntimeError('Open mechanical/revF/Filo36.FCStd first.')
doc.recompute()
metadata=json.loads((ROOT/'design/revF.json').read_text())
report={'scope':'Native FreeCAD nominal study; not a manufacturing release','halves':{},'unresolved':[
    'No routed PCB or integrated firmware', 'Actual module/socket/contact dimensions and retention',
    'Battery cable routing, strain relief and bending radii', 'Window tolerance and PCB copper-to-edge rule',
    'Printed fits, insertion/extraction loads, charging, RF and measured power']}
metadata['parts']={}
metadata['parameter_values_mm']={a:getattr(doc.Parameters,a).Value for a in metadata['parameters']}
for side,prefix in [('left','L_'),('right','R_')]:
    assembly=doc.getObject(prefix+'Half'); old=assembly.Placement
    assembly.Placement=A.Placement();doc.recompute()
    objects=[o for o in doc.Objects if hasattr(o,'PartID') and o.PartID.startswith(side+'-')]
    shapes={o.PartID[len(side)+1:]:o.Shape for o in objects}
    for o in objects:
        shape=o.Shape
        assert not shape.isNull() and shape.isValid(),(o.Name,'invalid shape')
        if o.PrototypePrintable:assert len(shape.Solids)==1,(o.PartID,'disconnected solids',len(shape.Solids))
        name=o.PartID
        mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.03,AngularDeflection=.12,Relative=False)
        if o.PrototypePrintable:assert mesh.isSolid(),(name,'open mesh')
        mesh.write(str(OUT/(name+'.stl')))
        if o.PrototypePrintable:shape.exportStep(str(OUT/(name+'.step')))
        b=shape.BoundBox
        metadata['parts'][name]={'object':o.Name,'role':o.Label,'group':o.Layer,'prototype_part':o.PrototypePrintable,
            'bounds_mm':[b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax],
            'stl_sha256':hashlib.sha256((OUT/(name+'.stl')).read_bytes()).hexdigest()}
    # Pair checks include real PCB battery opening and mounting holes.
    issues=[];pairs={}
    for i,(a,sa) in enumerate(shapes.items()):
        for b,sb in list(shapes.items())[i+1:]:
            v=sa.common(sb).Volume
            if v>.001:issues.append({'a':a,'b':b,'volume_mm3':round(v,6)})
            pairs[a+' / '+b]=round(v,6)
    compound=Part.makeCompound(list(shapes.values()));compound.exportStep(str(OUT/(side+'-assembly.step')))
    b=compound.BoundBox
    # North is max CAD Y, i.e. smallest KiCad Y.
    electronics=[shapes[k] for k in ['electronics-lid','mcu','display','battery','cradle','mcu-riser','display-sled','mcu-sockets','jst','slider','reset']]
    north=-max(s.BoundBox.YMax for s in electronics)
    report['halves'][side]={'pair_intersections_mm3':pairs,'collisions':issues,
        'assembly_bounds_mm':[b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax],
        'case_bounds_mm':[getattr(shapes['tray'].BoundBox,k) for k in ['XMin','YMin','ZMin','XMax','YMax','ZMax']],
        'electronics_north_kicad_y_mm':north,'frame_top_mm':shapes['electronics-lid'].BoundBox.ZMax,
        'display_top_mm':shapes['display'].BoundBox.ZMax,
        'adjacent_key_north_y_mm':10.755147934,'electronics_overhang_adjacent_mm':max(0,10.755147934-north),
        'battery_to_usb_vertical_gap_mm':doc.Parameters.MCUBottom.Value-1.6-(doc.Parameters.BatteryBottom.Value+3.8),
        'cradle_to_opening_per_side_mm':doc.Parameters.SlotClearance.Value,
        'nominal_copper_to_opening_mm':.37-doc.Parameters.SlotClearance.Value}
    metadata['halves'][side]['size_mm']=[b.XLength,b.YLength]
    assembly.Placement=old
    print(side,'parts',len(objects),'collisions',issues,flush=True)
doc.recompute()
metadata['inputs']=[{'path':p,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()} for p in [
    'design/layout.json','design/revF-profiles.json','tools/freecad/build_native.py','tools/freecad/export_native.py']]
metadata['fcstd_sha256']=hashlib.sha256((OUT/'Filo36.FCStd').read_bytes()).hexdigest()
(ROOT/'design/revF.json').write_text(json.dumps(metadata,indent=2)+'\n')
(ROOT/'validation/revF-mechanical.json').write_text(json.dumps(report,indent=2)+'\n')
assert not any(v['collisions'] for v in report['halves'].values()),'Unresolved nominal intersections; see validation/revF-mechanical.json'
print('PASS: native solids, closed printable meshes, nominal part intersections',flush=True)
