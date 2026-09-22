"""Export the active revI FCStd, preserving manual changes in the source document.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import hashlib
import json
from pathlib import Path
import FreeCAD as A
import Part
import MeshPart

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'mechanical/revI'
doc=A.ActiveDocument
if not doc or not doc.getObject('Parameters'):
    raise RuntimeError('Open mechanical/revI/Filo36.FCStd first.')
doc.recompute()
metadata=json.loads((ROOT/'design/revI.json').read_text())
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
    objects=[o for o in objects if assembly.DisplayCoverInstalled or o.Layer!='lid']
    shapes={o.PartID[len(side)+1:]:o.Shape for o in objects}
    active=doc.getObject(prefix+'ActiveBattery');reference=active.LinkedObject.Shape
    assert all(abs(getattr(shapes['battery'].BoundBox,k)-getattr(reference.BoundBox,k))<1e-6 for k in ['XMin','YMin','ZMin','XMax','YMax','ZMax']),(side,'active battery placement differs from profile')
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
            if v>.001:
                screw=a if a.startswith('screw-') else b if b.startswith('screw-') else None
                # Only the deliberate tapped M2 thread envelope may overlap.
                allowed=0
                if screw and 'tray' in (a,b):
                    index=int(screw.split('-')[-1])-1
                    spec=json.loads((ROOT/'design/revI-mounts.json').read_text())['left'][index]
                    x,y=spec['xy'];x=x if side=='left' else 160-x
                    tip=spec['seat_z']-spec['length']
                    thread=Part.makeCylinder(1,3.8-tip,A.Vector(x,-y,tip))
                    allowed=sa.common(sb).common(thread).Volume
                if v-allowed>.001:issues.append({'a':a,'b':b,'volume_mm3':round(v,6),'allowed_thread_volume_mm3':round(allowed,6)})
            pairs[a+' / '+b]=round(v,6)
    battery_checks={}
    for obj in [o for o in doc.Objects if hasattr(o,'BatteryStyle') and o.TypeId!='App::Link' and o.Name.startswith(prefix)]:
        shape=obj.Shape;ident=obj.BatteryStyle
        mm=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.03,AngularDeflection=.12,Relative=False)
        mm.write(str(OUT/(side+'-battery-'+ident+'.stl')))
        hits={n:round(shape.common(other).Volume,6) for n,other in shapes.items() if n!='battery' and shape.common(other).Volume>.001}
        assert not hits,(side,ident,hits)
        battery_checks[ident]={'component_collisions_mm3':hits,'bounds_mm':[getattr(shape.BoundBox,k) for k in ['XMin','YMin','ZMin','XMax','YMax','ZMax']]}
    # Check every interchangeable cover, not just the selected frame.
    frame_checks={}
    for obj in [o for o in doc.Objects if hasattr(o,'FrameStyle') and o.Name.startswith(prefix)]:
        shape=obj.Shape;assert shape.isValid() and len(shape.Solids)==1,(obj.Name,'invalid cover')
        frame_mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.03,AngularDeflection=.12,Relative=False)
        assert frame_mesh.isSolid();name=side+'-frame-'+obj.FrameStyle
        frame_mesh.write(str(OUT/(name+'.stl')));shape.exportStep(str(OUT/(name+'.step')))
        hits={n:round(shape.common(s).Volume,6) for n,s in shapes.items() if n!='electronics-lid' and shape.common(s).Volume>.001}
        # Nominal 12 x 5 mm USB plug envelope + straight insertion corridor.
        px=116.8 if side=='left' else 160-128.8
        plug=Part.makeBox(12,20,5,A.Vector(px,-18.8,6.7))
        hit=shape.common(plug).Volume
        frame_checks[obj.FrameStyle]={'component_collisions_mm3':hits,'usb_envelope_collision_mm3':round(hit,6),'volume_mm3':shape.Volume,'closed_mesh':True}
        assert not hits and hit<.001,(name,frame_checks[obj.FrameStyle])
    case_checks={}
    for style in json.loads((ROOT/'design/cases.json').read_text())['styles']:
        pair={g:doc.getObject(prefix+'Case_'+style+'_'+g).Shape for g in ['base','plate']}
        hits={}
        for group,shape in pair.items():
            assert shape.isValid() and len(shape.Solids)==1,(side,style,group,'invalid case')
            mm=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.03,AngularDeflection=.12,Relative=False)
            assert mm.isSolid(),(side,style,group,'open case mesh')
            name=side+'-case-'+style+'-'+group
            mm.write(str(OUT/(name+'.stl')));shape.exportStep(str(OUT/(name+'.step')))
            for name,other in shapes.items():
                if name in ['tray','key-plate']:continue
                common=shape.common(other);hit=common.Volume
                if group=='base' and name.startswith('screw-') and hit>.001:
                    spec=json.loads((ROOT/'design/revI-mounts.json').read_text())['left'][int(name.split('-')[-1])-1]
                    x,y=spec['xy'];x=x if side=='left' else 160-x;tip=spec['seat_z']-spec['length']
                    hit-=common.common(Part.makeCylinder(1,3.8-tip,A.Vector(x,-y,tip))).Volume
                if hit>.001:hits[group+' / '+name]=hit
            for frame in [o for o in doc.Objects if o.Name.startswith(prefix) and hasattr(o,'FrameStyle') and o.TypeId!='App::Link']:
                hit=shape.common(frame.Shape).Volume
                if hit>.001:hits[group+' / frame '+frame.FrameStyle]=hit
        hit=pair['base'].common(pair['plate']).Volume
        if hit>.001:hits['base / plate']=hit
        assert not hits,(side,style,hits)
        case_checks[style]={'closed_meshes':True,'connected_solids':True,'component_collisions_mm3':hits,
            'base_volume_mm3':pair['base'].Volume,'plate_volume_mm3':pair['plate'].Volume}
    compound=Part.makeCompound(list(shapes.values()));compound.exportStep(str(OUT/(side+'-assembly.step')))
    b=compound.BoundBox
    # North is max CAD Y, i.e. smallest KiCad Y.
    electronics=[shapes[k] for k in ['electronics-lid','mcu','display','battery','cradle','mcu-riser','display-sled','mcu-sockets','jst','slider','reset'] if k in shapes]
    north=-max(s.BoundBox.YMax for s in electronics)
    report['halves'][side]={'case_variants':case_checks,'display_cover_installed':assembly.DisplayCoverInstalled,'battery_variants':battery_checks,'frame_variants':frame_checks,'pair_intersections_mm3':pairs,'collisions':issues,
        'assembly_bounds_mm':[b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax],
        'case_bounds_mm':[getattr(shapes['tray'].BoundBox,k) for k in ['XMin','YMin','ZMin','XMax','YMax','ZMax']],
        'electronics_north_kicad_y_mm':north,'frame_top_mm':shapes['electronics-lid'].BoundBox.ZMax if 'electronics-lid' in shapes else None,
        'display_top_mm':shapes['display'].BoundBox.ZMax,
        'adjacent_key_north_y_mm':10.755147934,'electronics_overhang_adjacent_mm':max(0,10.755147934-north),
        'battery_to_usb_vertical_gap_mm':doc.Parameters.MCUBottom.Value-1.6-(doc.Parameters.BatteryBottom.Value+3.8),
        'cage_to_opening_per_side_mm':doc.Parameters.SlotClearance.Value,
        'nominal_copper_to_opening_mm':.62-doc.Parameters.SlotClearance.Value}
    metadata['halves'][side]['size_mm']=[b.XLength,b.YLength]
    assembly.Placement=old
    print(side,'parts',len(objects),'collisions',issues,flush=True)
doc.recompute()
metadata['inputs']=[{'path':p,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()} for p in [
    'design/cases.json','tools/keycap_config.py','tools/freecad/configuration.py','design/layout.json','design/revI-profiles.json','design/revI-frame-profiles.json','keycaps/catalog.json','design/revI-mounts.json','design/batteries.json','design/revI-magnets.json','design/revI-wire-study.json','tools/freecad/build_revI.py','tools/freecad/export_revI.py']]
metadata['fcstd_sha256']=hashlib.sha256((OUT/'Filo36.FCStd').read_bytes()).hexdigest()
(ROOT/'design/revI.json').write_text(json.dumps(metadata,indent=2)+'\n')
(ROOT/'validation/revI-mechanical.json').write_text(json.dumps(report,indent=2)+'\n')
assert not any(v['collisions'] for v in report['halves'].values()),'Unresolved nominal intersections; see validation/revI-mechanical.json'
print('PASS: native solids, closed printable meshes, nominal part intersections',flush=True)
