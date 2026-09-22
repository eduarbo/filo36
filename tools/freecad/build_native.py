"""Build the editable revF study using only native FreeCAD features.

Run with FreeCAD's Python (see docs/freecad.md). Opening/recomputing the saved
FCStd does not need this script, CadQuery, StepUp, or any custom Python proxy.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import json
import math
import sys
from pathlib import Path

import FreeCAD as A
import FreeCADGui as G
import Part
import Sketcher
import Mesh

def progress(*args, **kwargs):
    sys.__stdout__.write(" ".join(map(str,args))+"\n"); sys.__stdout__.flush()
print=progress

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'mechanical/revF'
OUT.mkdir(parents=True, exist_ok=True)
import faulthandler
faulthandler.enable()
G.showMainWindow()
print('GUI ready',flush=True)
doc = A.newDocument('Filo36_revF')
doc.Label = 'Filo36 · revF · estudio editable'
doc.Comment = 'GPL-3.0-or-later; Piantor/beekeeb, KLP Lame/braindefender CC-BY-SA-4.0. Nominal study, not manufacturing release.'
layout = json.loads((ROOT / 'design/layout.json').read_text())
profiles = json.loads((ROOT / 'design/revF-profiles.json').read_text())
params = doc.addObject('Spreadsheet::Sheet', 'Parameters')
params.Label = '00 · Parámetros (editar columna B)'
values = [
    ('Floor', 1.4, 'Suelo de base'), ('PlateThickness', 1.3, 'Espesor plate'),
    ('PlateBottom', 6.3, 'Cota inferior plate'), ('PCBTop', 5.4, 'Cara superior PCB'),
    ('PCBThickness', 1.6, 'Espesor PCB'), ('MCUShiftY', 7.5, 'Micro hacia pulgares'),
    ('MCUBottom', 8.8, 'Cara inferior placa del micro'),
    ('DisplayShiftY', 2.4, 'Pantalla hacia pulgares'),
    ('DisplayBottom', 14.2, 'Cara inferior PCB pantalla'),
    ('BatteryShiftY', 2.0, 'Batería hacia pulgares'), ('BatteryBottom', 2.0, 'Base celda'),
    ('FrameTop', 16.6, 'Altura máxima marco abierto'),
    ('SlotClearance', .15, 'Holgura cuna a abertura, POR LADO'),
]
cells = {}
for row, (alias, number, note) in enumerate(values, 2):
    params.set(f'A{row}', alias); params.set(f'B{row}', f'{number} mm')
    params.setAlias(f'B{row}', alias); params.set(f'C{row}', note); cells[alias] = f'B{row}'
params.set('A1', 'Parámetro'); params.set('B1', 'Valor'); params.set('C1', 'Uso')
params.setColumnWidth('A', 165); params.setColumnWidth('B', 95); params.setColumnWidth('C', 290)
params.setStyle('A1:C1', 'bold'); params.setBackground('B2:B14', (0.84, .95, .88))
doc.recompute()
print('Parameters ready',flush=True)
finals = {}
metadata = {'revision': 'F', 'units': 'mm', 'coordinate_system': 'FreeCAD X=KiCad X, Y=-KiCad Y; PCB top=5.4 mm',
            'manufacturing_ready': False, 'parameters': cells, 'halves': {}, 'parts': {}}


def expr(obj, prop, expression):
    obj.setExpression(prop, expression)


for side in ('left', 'right'):
    print('Building',side,flush=True)
    prefix = 'L_' if side == 'left' else 'R_'
    assembly = doc.addObject('App::Part', prefix + 'Half')
    assembly.Label = '01 · Izquierda' if side == 'left' else '02 · Derecha'
    history = doc.addObject('App::DocumentObjectGroup', prefix + 'Construction')
    history.Label = 'Construcción · croquis y operaciones'; assembly.addObject(history)
    finished = []
    mx = lambda x: x if side == 'left' else 160 - x

    def add(typ, name):
        obj = doc.addObject(typ, prefix + name); history.addObject(obj); return obj

    def box(name, x0, y0, x1, y1, z, height, shift=None):
        obj = add('Part::Box', name)
        obj.Length = x1 - x0; obj.Width = y1 - y0; obj.Height = height
        obj.Placement.Base = A.Vector(x0 if side == 'left' else 160 - x1, -y1, z)
        if shift:
            expr(obj, 'Placement.Base.y', f'-{y1} mm - Parameters.{shift}')
        return obj

    def cyl(name, x, y, z, radius, height):
        o = add('Part::Cylinder', name); o.Radius = radius; o.Height = height
        o.Placement.Base = A.Vector(mx(x), -y, z); return o

    def sketch(name, points, plane='XY', rail=False):
        s = add('Sketcher::SketchObject', name)
        vectors = [A.Vector(x, -y, 0) for x, y in points] if plane == 'XY' else [A.Vector(y, z, 0) for y,z in points]
        for a,b in zip(vectors, vectors[1:] + vectors[:1]):
            i = s.addGeometry(Part.LineSegment(a, b), False)
            if not rail:s.addConstraint(Sketcher.Constraint('Block', i))
        if rail:
            for i,v in enumerate(vectors):
                s.addConstraint(Sketcher.Constraint('Coincident',i,2,(i+1)%len(vectors),1))
                s.addConstraint(Sketcher.Constraint('DistanceX',i,1,v.x))
                c=s.addConstraint(Sketcher.Constraint('DistanceY',i,1,v.y))
                if v.y in (16.6,15.4):s.setExpression(f'Constraints[{c}]','Parameters.FrameTop' + (' - 1.2 mm' if v.y==15.4 else ''))
        return s

    def extrude(name, points, z, height):
        s = sketch(name + 'Sketch', points)
        e = add('Part::Extrusion', name); e.Base = s; e.Dir = A.Vector(0,0,1)
        e.LengthFwd = height; e.Solid = True; e.Placement.Base.z = z
        return e

    def fuse(name, objects):
        o = add('Part::MultiFuse', name); o.Shapes = objects; o.Refine = True; return o

    def cut(name, base, tool):
        o = add('Part::Cut', name); o.Base = base; o.Tool = tool; o.Refine = True; return o

    def done(name, obj, label, group, color, printable=False):
        assembly.addObject(obj); finished.append(obj)
        obj.Label = label
        obj.addProperty('App::PropertyString', 'PartID', 'Filo36'); obj.PartID = side + '-' + name
        obj.addProperty('App::PropertyString', 'Layer', 'Filo36'); obj.Layer = group
        obj.addProperty('App::PropertyBool', 'PrototypePrintable', 'Filo36'); obj.PrototypePrintable = printable
        obj.addProperty('App::PropertyString', 'ModelStatus', 'Filo36'); obj.ModelStatus = 'Estudio nominal; encaje físico pendiente'
        obj.ViewObject.ShapeColor = color; obj.ViewObject.LineColor = (.13,.18,.17)
        finals[side + '-' + name] = obj
        return obj

    print(side,'helpers ready',flush=True)
    # Native sketch/extrusion/boolean history; stored source contour is editable.
    outer = extrude('OuterPad', profiles[side]['outer'], 0, 6.3)
    cavity = extrude('Cavity', profiles[side]['inner'], 1.4, 8)
    expr(cavity, 'Placement.Base.z', 'Parameters.Floor')
    tray = cut('TrayShell', outer, cavity)
    mounts = [(21,37.5),(57,20.5),(41.2,66.6),(130.6,64),(114.5,64)]
    radii = [2.5,1.8,2.3,2.1,2.1]
    holes = []
    for i, ((x,y),radius) in enumerate(zip(mounts,radii),1):
        pillar = cyl('Pillar'+str(i),x,y,1.4,radius,2.4)
        expr(pillar, 'Placement.Base.z', 'Parameters.Floor')
        expr(pillar, 'Height', 'Parameters.PCBTop - Parameters.PCBThickness - Parameters.Floor')
        tray = fuse('TrayPillar'+str(i), [tray,pillar])
        tray = cut('TrayDrill'+str(i),tray,cyl('Pilot'+str(i),x,y,-.1,.85,4.2))
        washer = cut('Washer'+str(i),cyl('Spacer'+str(i),x,y,5.4,radius,.9),cyl('SpacerHole'+str(i),x,y,5.3,1.15,1.1))
        done('washer-'+str(i),washer,'Arandela '+str(i),'fasteners',(.54,.57,.54),True)
        holes.append(cyl('BoardDrill'+str(i),x,y,3.7,1.1,2))
        tray=cut('WasherSeat'+str(i),tray,cyl('WasherSeatTool'+str(i),x,y,5.4,radius+.1,1.0))
    power_slot = box('PowerAccess',128.3,53.4,140,61.9,5.1,4.1)
    tray = cut('TrayPowerCut',tray,power_slot)
    done('tray',tray,'Base · suelo editable','base',(.105,.145,.15),True)

    plate = extrude('PlatePad',profiles[side]['plate'],6.3,1.3)
    expr(plate,'Placement.Base.z','Parameters.PlateBottom'); expr(plate,'LengthFwd','Parameters.PlateThickness')
    for key in layout['halves'][side]:
        angle = -math.radians(key['angle']); points=[]
        for x,y in [(-7,-7),(7,-7),(7,7),(-7,7)]:
            points.append((key['x']+x*math.cos(angle)-y*math.sin(angle),key['y']+x*math.sin(angle)+y*math.cos(angle)))
        plate=cut('Plate_'+key['ref'],plate,extrude('SwitchCut_'+key['ref'],points,5.5,4))
    for i,(x,y) in enumerate(mounts[:3],1):plate=cut('PlateDrill'+str(i),plate,cyl('PlateHole'+str(i),x,y,5.5,1.15,4))
    done('key-plate',plate,'Plate · espesor editable','plate',(.145,.205,.207),True)

    pcb=extrude('PCBPad',profiles[side]['pcb_outline'],3.8,1.6)
    expr(pcb,'LengthFwd','Parameters.PCBThickness');expr(pcb,'Placement.Base.z','Parameters.PCBTop - Parameters.PCBThickness')
    slot=box('BatteryOpening',116.25,12.45,129.35,44.95,3.6,2.2,'BatteryShiftY')
    expr(slot,'Length','12.8 mm + 2 * Parameters.SlotClearance')
    expr(slot,'Width','32.2 mm + 2 * Parameters.SlotClearance')
    expr(slot,'Placement.Base.x',('116.4 mm - Parameters.SlotClearance' if side=='left' else '30.8 mm - Parameters.SlotClearance'))
    expr(slot,'Placement.Base.y','-44.8 mm - Parameters.BatteryShiftY - Parameters.SlotClearance')
    pcb=cut('PCBBatteryOpening',pcb,slot)
    for i,h in enumerate(holes,1):pcb=cut('PCBMount'+str(i),pcb,h)
    drills_path=ROOT/'design/revF-drills.json'
    if drills_path.exists():
        drills=[]
        for i,d in enumerate(json.loads(drills_path.read_text())[side]):
            if d['ref'].startswith('H'):continue
            o=add('Part::Cylinder','PadDrill'+str(i));o.Radius=d['radius'];o.Height=2
            o.Placement.Base=A.Vector(d['x'],-d['y'],3.7)
            if d['ref']=='U1':expr(o,'Placement.Base.y',f'{7.5-d["y"]} mm - Parameters.MCUShiftY')
            if d['ref']=='J2':expr(o,'Placement.Base.y',f'{2.4-d["y"]} mm - Parameters.DisplayShiftY')
            drills.append(o)
        tool=add('Part::Compound','DrillTools');tool.Links=drills
        pcb=cut('PCBAllDrills',pcb,tool)
    done('pcb',pcb,'PCB · colocación sin ruteo','pcb',(.10,.34,.25))

    print(side,'case and PCB defined',flush=True)
    # Battery is lowered into an actual opening in the PCB, independent of MCU.
    cradle=box('CradleOuter',116.4,12.6,129.2,44.8,1.4,4.8,'BatteryShiftY')
    cavity=box('CradleCavity',116.8,13.0,128.8,44.4,2,5,'BatteryShiftY')
    expr(cavity,'Placement.Base.z','Parameters.BatteryBottom')
    cradle=cut('CradleHollow',cradle,cavity)
    cradle=cut('CableExit',cradle,box('CableExitTool',120,44,126,46,3.4,3,'BatteryShiftY'))
    done('cradle',cradle,'Cuna aislante rebajada','supports',(.44,.57,.52),True)
    cell=box('Cell',117.05,13.2,128.55,44.2,2,3.8,'BatteryShiftY')
    expr(cell,'Placement.Base.z','Parameters.BatteryBottom')
    done('battery',cell,'LiPo 100 mAh · referencia','battery',(.72,.75,.74))
    keeper=fuse('BatteryKeeper',[
        box('KeeperA',116.4,12.6,129.2,13.7,6.2,.6,'BatteryShiftY'),
        box('KeeperB',116.4,43.7,129.2,44.8,6.2,.6,'BatteryShiftY'),
        box('KeeperSideA',116.4,12.6,116.9,44.8,6.2,.6,'BatteryShiftY'),
        box('KeeperSideB',128.7,12.6,129.2,44.8,6.2,.6,'BatteryShiftY')])
    done('battery-retainer',keeper,'Retenedor · fijación por prototipar','supports',(.44,.57,.52),True)

    bars=[]
    for i,(a,b) in enumerate([(112.9,114),(131.6,132.7)]):
        bar=box('Riser'+str(i),a,8,b,40.3,5.4,3.4,'MCUShiftY');expr(bar,'Height','Parameters.MCUBottom - Parameters.PCBTop');bars.append(bar)
    bars.append(box('RiserBridge',112.9,39.5,132.7,40.3,5.4,.8,'MCUShiftY'))
    done('mcu-riser',fuse('Riser',bars),'Soporte independiente del micro','supports',(.31,.43,.39),True)
    board=box('MCUBoard',113.3,4.3,132.3,40.3,8.8,1,'MCUShiftY')
    expr(board,'Placement.Base.z','Parameters.MCUBottom')
    chips=box('MCUChips',115.3,11,130.3,34,9.8,2.6,'MCUShiftY');expr(chips,'Placement.Base.z','Parameters.MCUBottom + 1 mm')
    usb=box('USB',117.8,3.3,127.8,12,7.2,3.2,'MCUShiftY');expr(usb,'Placement.Base.z','Parameters.MCUBottom - 1.6 mm')
    done('mcu',fuse('MCUModule',[board,chips,usb]),'nice!nano + USB · referencia','mcu',(.075,.23,.18))
    sock=[]
    for i,x in enumerate([115.18,130.42]):sock.append(box('Socket'+str(i),x-.9,8.53,x+.9,39.01,5.4,2.413,'MCUShiftY'))
    socketcompound=add('Part::Compound','MCUSockets');socketcompound.Links=sock
    done('mcu-sockets',socketcompound,'Sockets del micro · referencia','connectors',(.16,.21,.18))

    sled=box('DisplayPost',115.4,46.4,130.2,50.4,5.4,8.8,'DisplayShiftY')
    expr(sled,'Height','Parameters.DisplayBottom - Parameters.PCBTop')
    sled=cut('HeaderRelief',sled,box('HeaderReliefTool',116.2,46.9,129.4,49.9,5.3,2.95,'DisplayShiftY'))
    # Commercial display contact order remains left-to-right on BOTH halves.
    for i in range(5):
        h=add('Part::Cylinder','DisplayContact'+str(i));h.Radius=.42;h.Height=12
        h.Placement.Base=A.Vector(mx(122.8)-5.08+2.54*i,-50.8,5.2)
        expr(h,'Placement.Base.y','-48.4 mm - Parameters.DisplayShiftY');sled=cut('SledHole'+str(i),sled,h)
    members=[sled]
    for i,b in enumerate([(115,13.1,116.3,50.4),(129.3,13.1,130.6,50.4),(115,13.1,130.6,14.1)]):
        o=box('DisplayLedge'+str(i),*b,13.8,.4,'DisplayShiftY');expr(o,'Placement.Base.z','Parameters.DisplayBottom - .4 mm');members.append(o)
    for i,b in enumerate([(115,13.1,115.55,50.4),(130.05,13.1,130.6,50.4)]):
        o=box('DisplaySide'+str(i),*b,13.8,1.6,'DisplayShiftY');expr(o,'Placement.Base.z','Parameters.DisplayBottom - .4 mm');members.append(o)
    done('display-sled',fuse('DisplaySled',members),'Soporte de pantalla · desmontable','supports',(.32,.43,.39),True)
    screenparts=[]
    for name,b,z,h in [('DisplayPCB',(115.7,13.6,129.9,49.8),0,1),('DisplayGlass',(115.95,16.25,129.65,46.55),1,.9),('DisplayUnderside',(116.8,23.25,128.8,42.25),-1,1)]:
        o=box(name,*b,14.2+z,h,'DisplayShiftY');expr(o,'Placement.Base.z',f'Parameters.DisplayBottom + {z} mm');screenparts.append(o)
    done('display',fuse('Screen',screenparts),'nice!view completa · referencia','display',(.07,.14,.11))
    done('jst',box('JST',112.5,54.2,119.1,60.5,5.4,8.5),'JST · referencia recolocada','connectors',(.85,.83,.73))
    done('reset',box('Reset',120,56.5,126,62.5,5.4,2.5),'Reset · referencia recolocada','connectors',(.33,.36,.32))
    done('slider',box('Slider',128.5,53.9,136.5,61.4,5.4,2.5),'Encendido · referencia recolocada','connectors',(.29,.34,.31))

    print(side,'electronics defined',flush=True)
    # Open side rails replace the tall closed hood; rear screws leave USB free.
    # YZ rail profiles are sketches; frame height is a native scale-independent
    # top extension controlled by FrameTop, with diagonal end braces.
    rails=[]
    railpoints=[(11,6.3),(11,7),(23,16.6),(52,16.6),(65.5,9),(68.5,6.3),
                (61.5,6.3),(51.5,15.4),(23.5,15.4),(13,6.3)]
    for i,(x0,x1) in enumerate([(111,112.2),(133.8,135)]):
        s=sketch('RailProfile'+str(i),railpoints,plane='YZ',rail=True)
        # Local sketch x = KiCad Y, local y = height; extrusion points across X.
        s.Placement=A.Placement(A.Vector(mx(x0 if side=='left' else x1),0,0),A.Rotation(A.Vector(0,-1,0),A.Vector(0,0,1),A.Vector(-1,0,0),'ZXY'))
        e=add('Part::Extrusion','Rail'+str(i));e.Base=s;e.Dir=A.Vector(1,0,0);e.LengthFwd=x1-x0;e.Solid=True;rails.append(e)
    rails += [box('FrontBridge',111,11,135,12,6.3,.7),box('RearBridge',111,62.8,135,66,6.3,2.7)]
    frame=fuse('OpenFrame',rails)
    frame=cut('FramePowerCut',frame,power_slot)
    for i,(x,y) in enumerate(mounts[3:],4):
        frame=fuse('FramePillar'+str(i),[frame,cyl('FrameBoss'+str(i),x,y,6.3,2.1,2.7)])
        frame=cut('FrameHole'+str(i),frame,cyl('FrameDrill'+str(i),x,y,6.2,1.15,3))
    clip=add('Part::Common','FrameOutlineClip');clip.Base=frame;clip.Tool=extrude('FrameBoundary',profiles[side]['hood'],6.2,14);frame=clip
    done('electronics-lid',frame,'Marco abierto · USB y laterales visibles','lid',(.16,.25,.23),True)

    print(side,'frame defined; recompute BEFORE meshes',flush=True)
    doc.recompute()
    print(side,'solid recompute complete',flush=True)
    # Keycaps remain the original KLP meshes; mirrored local Y is the KiCad/CAD
    # coordinate conversion, not a redesign of the keycap.
    keygroup=doc.addObject('App::DocumentObjectGroup',prefix+'Keys');keygroup.Label='Teclas · centros y ángulos Piantor';assembly.addObject(keygroup)
    for key in layout['halves'][side]:
        cap='thumb' if key['row']==3 else 'normal_homing' if key['ref']=='K14' else 'normal'
        o=doc.addObject('Mesh::Feature',prefix+key['ref']); keygroup.addObject(o)
        mesh=Mesh.Mesh(str(ROOT/'keycaps'/f'{cap}.stl')); mat=A.Matrix();mat.A22=-1;mesh.transform(mat);mesh.flipNormals();o.Mesh=mesh
        o.Placement=A.Placement(A.Vector(key['x'],-key['y'],12.2),A.Rotation(A.Vector(0,0,1),key['angle']))
        o.Label='KLP '+key['ref'];o.ViewObject.ShapeColor=(.25,.55,.45) if key['row']==3 else (.91,.878,.783)
        o.addProperty('App::PropertyString','Source','Filo36');o.Source='KLP Lame / braindefender / CC-BY-SA-4.0 / mesh unchanged; seating illustrative'
    print(side,'recomputing',flush=True)
    doc.recompute()
    print(side,'recomputed',flush=True)
    for o in history.Group:o.Visibility=False
    for o in finished:o.Visibility=True
    history.Visibility=False
    metadata['halves'][side]={'mount_holes':[[mx(x),y] for x,y in mounts], 'mount_tops_z':[7.6,7.6,7.6,9,9],
        'outer':profiles[side]['outer'],'pcb_outline':profiles[side]['pcb_outline'],
        'battery_opening':[mx(116.25) if side=='left' else mx(129.35),14.45,mx(129.35) if side=='left' else mx(116.25),46.95],
        'display_header':{'x':mx(122.8)-5.08,'y':50.8}, 'electronics_cover':profiles[side]['hood']}
    if side=='right':assembly.Placement.Base.x=161

doc.recompute()
G.activeDocument().activeView().viewTop();G.activeDocument().activeView().fitAll()
doc.saveAs(str(OUT/'Filo36.FCStd'))
(ROOT/'design/revF.json').write_text(json.dumps(metadata,indent=2)+'\n')
print('Saved native editable FreeCAD assembly:',OUT/'Filo36.FCStd',flush=True)
exec(compile((ROOT/'tools/freecad/export_native.py').read_text(),str(ROOT/'tools/freecad/export_native.py'),'exec'))
