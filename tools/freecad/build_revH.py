"""Build the editable revH study using only native FreeCAD features.

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
OUT = ROOT / 'mechanical/revH'
OUT.mkdir(parents=True, exist_ok=True)
import faulthandler
faulthandler.enable()
G.showMainWindow()
print('GUI ready',flush=True)
doc = A.newDocument('Filo36_revH')
doc.Label = 'Filo36 · revH · editable study'
doc.Comment = 'GPL-3.0-or-later; Piantor/beekeeb, KLP Lame/braindefender CC-BY-SA-4.0. Nominal study, not manufacturing release.'
layout = json.loads((ROOT / 'design/layout.json').read_text())
profiles = json.loads((ROOT / 'design/revH-profiles.json').read_text())
params = doc.addObject('Spreadsheet::Sheet', 'Parameters')
params.Label = '00 · Parameters (edit column B)'
values = [
    ('Floor', 1.4, 'Base floor'), ('PlateThickness', 1.3, 'Plate thickness'),
    ('PlateBottom', 6.3, 'Plate bottom Z'), ('PCBTop', 5.4, 'PCB top'),
    ('PCBThickness', 1.6, 'PCB thickness'), ('MCUShiftY', 7.5, 'Controller shift toward thumbs'),
    ('MCUBottom', 8.8, 'Controller PCB bottom'),
    ('DisplayShiftY', 2.4, 'Display shift toward thumbs'),
    ('DisplayBottom', 14.2, 'Display PCB bottom'),
    ('BatteryShiftY', 2.0, 'Battery shift toward thumbs'), ('BatteryBottom', 2.0, 'Cell bottom'),
    ('FrameTop', 16.6, 'Frame top height'),
    ('FrameRoof', 1.2, 'Frame roof thickness'), ('WindowMargin', .4, 'Clearance per glass side'),
    ('SlotClearance', .15, 'Cradle/opening clearance PER SIDE'),
]
cells = {}
for row, (alias, number, note) in enumerate(values, 2):
    params.set(f'A{row}', alias); params.set(f'B{row}', f'{number} mm')
    params.setAlias(f'B{row}', alias); params.set(f'C{row}', note); cells[alias] = f'B{row}'
params.set('A1', 'Parameter'); params.set('B1', 'Value'); params.set('C1', 'Purpose')
params.setColumnWidth('A', 165); params.setColumnWidth('B', 95); params.setColumnWidth('C', 290)
params.setStyle('A1:C1', 'bold'); params.setBackground('B2:B16', (0.84, .95, .88))
doc.recompute()
print('Parameters ready',flush=True)
frame_profiles=json.loads((ROOT/'design/revH-frame-profiles.json').read_text())
sys.path.insert(0,str(ROOT/'tools'));from keycap_config import load,default_config,check
catalog=load();configuration=default_config(catalog);assert not check(configuration,catalog)[0]
variants={v['id']:v for v in catalog['variants']}
finals = {}
metadata = {'revision': 'H', 'units': 'mm', 'coordinate_system': 'FreeCAD X=KiCad X, Y=-KiCad Y; PCB top=5.4 mm',
            'manufacturing_ready': False, 'parameters': cells, 'halves': {}, 'parts': {}}


def expr(obj, prop, expression):
    obj.setExpression(prop, expression)


for side in ('left', 'right'):
    print('Building',side,flush=True)
    prefix = 'L_' if side == 'left' else 'R_'
    assembly = doc.addObject('App::Part', prefix + 'Half')
    assembly.Label = '01 · Left' if side == 'left' else '02 · Right'
    history = doc.addObject('App::DocumentObjectGroup', prefix + 'Construction')
    history.Label = 'Construction · sketches and operations'; assembly.addObject(history)
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
        # Native lines and arcs: the visible corner count is the control polygon,
        # not the tessellation needed for STL/PCB export.
        arcs=None
        if points==profiles[side]['outer']:arcs=profiles[side]['outer_arcs']
        elif points==frame_profiles[side]['outer']:arcs=frame_profiles[side]['outer_arcs']
        elif points==frame_profiles[side]['bevel']:arcs=frame_profiles[side]['bevel_arcs']
        elif points==frame_profiles[side]['facet']:arcs=frame_profiles[side]['facet_arcs']
        if arcs and plane=='XY':
            vec=lambda p:A.Vector(p[0],-p[1],0)
            for i,a in enumerate(arcs):
                j=s.addGeometry(Part.Arc(vec(a['start']),vec(a['mid']),vec(a['end'])),False)
                s.addConstraint(Sketcher.Constraint('Block',j))
                j=s.addGeometry(Part.LineSegment(vec(a['end']),vec(arcs[(i+1)%len(arcs)]['start'])),False)
                s.addConstraint(Sketcher.Constraint('Block',j))
            return s
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
        obj.addProperty('App::PropertyString', 'ModelStatus', 'Filo36'); obj.ModelStatus = 'Nominal study; physical fit untested'
        view=obj.LinkedObject.ViewObject if obj.TypeId=='App::Link' else obj.ViewObject
        view.ShapeColor = color; view.LineColor = (.13,.18,.17)
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
        done('washer-'+str(i),washer,'Washer '+str(i),'fasteners',(.54,.57,.54),True)
        holes.append(cyl('BoardDrill'+str(i),x,y,3.7,1.1,2))
        tray=cut('WasherSeat'+str(i),tray,cyl('WasherSeatTool'+str(i),x,y,5.4,radius+.1,1.0))
    power_slot = box('PowerAccess',128.3,53.4,140,61.9,5.1,4.1)
    tray = cut('TrayPowerCut',tray,power_slot)
    done('tray',tray,'Base · editable floor','base',(.105,.145,.15),True)

    plate = extrude('PlatePad',profiles[side]['plate'],6.3,1.3)
    expr(plate,'Placement.Base.z','Parameters.PlateBottom'); expr(plate,'LengthFwd','Parameters.PlateThickness')
    for key in layout['halves'][side]:
        angle = -math.radians(key['angle']); points=[]
        for x,y in [(-7,-7),(7,-7),(7,7),(-7,7)]:
            points.append((key['x']+x*math.cos(angle)-y*math.sin(angle),key['y']+x*math.sin(angle)+y*math.cos(angle)))
        plate=cut('Plate_'+key['ref'],plate,extrude('SwitchCut_'+key['ref'],points,5.5,4))
    for i,(x,y) in enumerate(mounts[:3],1):plate=cut('PlateDrill'+str(i),plate,cyl('PlateHole'+str(i),x,y,5.5,1.15,4))
    done('key-plate',plate,'Plate · editable thickness','plate',(.145,.205,.207),True)

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
    done('pcb',pcb,'PCB · unrouted placement','pcb',(.10,.34,.25))

    print(side,'case and PCB defined',flush=True)
    # Battery is lowered into an actual opening in the PCB, independent of MCU.
    cradle=box('CradleOuter',116.4,12.6,129.2,44.8,1.4,4.8,'BatteryShiftY')
    cavity=box('CradleCavity',116.8,13.0,128.8,44.4,2,5,'BatteryShiftY')
    expr(cavity,'Placement.Base.z','Parameters.BatteryBottom')
    cradle=cut('CradleHollow',cradle,cavity)
    cradle=cut('CableExit',cradle,box('CableExitTool',120,44,126,46,3.4,3,'BatteryShiftY'))
    done('cradle',cradle,'Recessed insulating cradle','supports',(.44,.57,.52),True)
    cell=box('Cell',117.05,13.2,128.55,44.2,2,3.8,'BatteryShiftY')
    expr(cell,'Placement.Base.z','Parameters.BatteryBottom')
    done('battery',cell,'LiPo 100 mAh · reference','battery',(.72,.75,.74))
    keeper=fuse('BatteryKeeper',[
        box('KeeperA',116.4,12.6,129.2,13.7,6.2,.6,'BatteryShiftY'),
        box('KeeperB',116.4,43.7,129.2,44.8,6.2,.6,'BatteryShiftY'),
        box('KeeperSideA',116.4,12.6,116.9,44.8,6.2,.6,'BatteryShiftY'),
        box('KeeperSideB',128.7,12.6,129.2,44.8,6.2,.6,'BatteryShiftY')])
    done('battery-retainer',keeper,'Retainer · fastening unprototyped','supports',(.44,.57,.52),True)

    bars=[]
    for i,(a,b) in enumerate([(112.9,114),(131.6,132.7)]):
        bar=box('Riser'+str(i),a,8,b,40.3,5.4,3.4,'MCUShiftY');expr(bar,'Height','Parameters.MCUBottom - Parameters.PCBTop');bars.append(bar)
    bars.append(box('RiserBridge',112.9,39.5,132.7,40.3,5.4,.8,'MCUShiftY'))
    done('mcu-riser',fuse('Riser',bars),'Independent controller support','supports',(.31,.43,.39),True)
    board=box('MCUBoard',113.3,4.3,132.3,40.3,8.8,1,'MCUShiftY')
    expr(board,'Placement.Base.z','Parameters.MCUBottom')
    chips=box('MCUChips',115.3,11,130.3,34,9.8,2.6,'MCUShiftY');expr(chips,'Placement.Base.z','Parameters.MCUBottom + 1 mm')
    usb=box('USB',117.8,3.3,127.8,12,7.2,3.2,'MCUShiftY');expr(usb,'Placement.Base.z','Parameters.MCUBottom - 1.6 mm')
    done('mcu',fuse('MCUModule',[board,chips,usb]),'nice!nano + USB · reference','mcu',(.075,.23,.18))
    sock=[]
    for i,x in enumerate([115.18,130.42]):sock.append(box('Socket'+str(i),x-.9,8.53,x+.9,39.01,5.4,2.413,'MCUShiftY'))
    socketcompound=add('Part::Compound','MCUSockets');socketcompound.Links=sock
    done('mcu-sockets',socketcompound,'Controller sockets · reference','connectors',(.16,.21,.18))

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
    done('display-sled',fuse('DisplaySled',members),'Removable display support','supports',(.32,.43,.39),True)
    screenparts=[]
    for name,b,z,h in [('DisplayPCB',(115.7,13.6,129.9,49.8),0,1),('DisplayGlass',(115.95,16.25,129.65,46.55),1,.9),('DisplayUnderside',(116.8,23.25,128.8,42.25),-1,1)]:
        o=box(name,*b,14.2+z,h,'DisplayShiftY');expr(o,'Placement.Base.z',f'Parameters.DisplayBottom + {z} mm');screenparts.append(o)
    done('display',fuse('Screen',screenparts),'Full nice!view · reference','display',(.07,.14,.11))
    done('jst',box('JST',112.5,54.2,119.1,60.5,5.4,8.5),'JST · relocated reference','connectors',(.85,.83,.73))
    done('reset',box('Reset',120,56.5,126,62.5,5.4,2.5),'Reset · relocated reference','connectors',(.33,.36,.32))
    done('slider',box('Slider',128.5,53.9,136.5,61.4,5.4,2.5),'Power switch · relocated reference','connectors',(.29,.34,.31))

    print(side,'electronics defined',flush=True)
    # Interchangeable opaque covers. Same PCB/mount centers and independent sled.
    # Three native ruled lofts share one cavity, screen aperture and service cuts.
    cavity=extrude('FrameInside',frame_profiles[side]['inner'],6.2,9.2)
    expr(cavity,'LengthFwd','Parameters.FrameTop - Parameters.FrameRoof - 6.2 mm')
    window=box('GlassWindow',115.55,18.25,130.05,49.35,15.3,5)
    expr(window,'Length','13.7 mm + 2 * Parameters.WindowMargin')
    expr(window,'Width','30.3 mm + 2 * Parameters.WindowMargin')
    expr(window,'Placement.Base.x',('115.95 mm - Parameters.WindowMargin' if side=='left' else '30.35 mm - Parameters.WindowMargin'))
    expr(window,'Placement.Base.y','-46.55 mm - Parameters.DisplayShiftY - Parameters.WindowMargin')
    expr(window,'Placement.Base.z','Parameters.DisplayBottom + .9 mm')
    usb_access=box('USBPlugAccess',116.3,8,129.3,20,6.2,5.6)
    mcu_clearance=box('MCUCornerClearance',113,3.9,132.6,40.6,8.5,4.2,'MCUShiftY')
    expr(mcu_clearance,'Placement.Base.z','Parameters.MCUBottom - .3 mm')
    reset_access=cyl('ResetToolAccess',123,59.5,7.8,1.4,12)
    styles={}
    for style,label in catalog['frame_styles'].items():
        if style in ('bevel','facet'):
            sections=[]
            for j,(z,contour) in enumerate([(6.3,'outer'),(15.4,'outer'),(16.6,style)]):
                sk=sketch('Frame_'+style+'_Section'+str(j),frame_profiles[side][contour]);sk.Placement.Base.z=z
                if j==1:expr(sk,'Placement.Base.z','Parameters.FrameTop - Parameters.FrameRoof')
                if j==2:expr(sk,'Placement.Base.z','Parameters.FrameTop')
                sections.append(sk)
            loft=add('Part::Loft','Frame_'+style+'_Loft');loft.Sections=sections;loft.Solid=True;loft.Ruled=True
        else:
            # Constant sections are extrusions. Redundant identical arc loft
            # sections can fail later boolean recomputes when FrameTop changes.
            loft=extrude('Frame_'+style+'_Pad',frame_profiles[side]['outer'],6.3,10.3)
            expr(loft,'LengthFwd','Parameters.FrameTop - 6.3 mm')
        cover=cut('Frame_'+style+'_Hollow',loft,cavity)
        cover=cut('Frame_'+style+'_Window',cover,window)
        cover=cut('Frame_'+style+'_USB',cover,usb_access)
        cover=cut('Frame_'+style+'_Micro',cover,mcu_clearance)
        cover=cut('Frame_'+style+'_Power',cover,power_slot)
        cover=cut('Frame_'+style+'_Reset',cover,reset_access)
        # Distinct printable themes. Relief is fused into the roof, stays inside
        # the common XY envelope and adds only 0.6 mm. Controls are decorative.
        relief=[]
        def badge_box(tag,x0,y0,x1,y1):
            b=box('Theme_'+style+'_'+tag,x0,y0,x1,y1,16.5,.7)
            expr(b,'Placement.Base.z','Parameters.FrameTop - .1 mm');relief.append(b)
        def badge_disc(tag,x,y,r):
            b=cyl('Theme_'+style+'_'+tag,x,y,16.5,r,.7)
            expr(b,'Placement.Base.z','Parameters.FrameTop - .1 mm');relief.append(b)
        if style=='handheld':
            badge_box('DpadH',113.7,54,120.1,56)
            badge_box('DpadV',115.9,51.8,117.9,58.2)
            badge_disc('ButtonA',129.3,53.5,1.65)
            badge_disc('ButtonB',125.7,56.1,1.65)
            for i in range(3):badge_box('Speaker'+str(i),119+i*2.2,63,120+i*2.2,65.3)
        elif style=='tv':
            # Portrait CRT-inspired bezel, sized around the actual LCD opening.
            badge_box('BezelLeft',113.8,16.8,115.55,50.8)
            badge_box('BezelRight',130.05,16.8,131.8,50.8)
            badge_box('BezelTop',113.8,16.8,131.8,18.25)
            badge_box('BezelBottom',113.8,49.35,131.8,50.8)
            badge_disc('Tuning',128.9,55.1,2.15)
            for i in range(4):badge_box('Speaker'+str(i),114.2,52.6+i*1.5,120,53.3+i*1.5)
        elif style=='cyberpunk':
            for i in range(3):
                badge_box('Vent'+str(i),113.4+i*2.7,52,114.6+i*2.7,56.9)
            badge_box('TraceA',126.8,51.8,132.5,52.6)
            badge_box('TraceB',131.7,52.6,132.5,58.1)
            badge_box('TraceC',126.8,57.3,132.5,58.1)
            badge_box('Panel',119.5,63.2,124.2,65.5)
            badge_disc('Node',128.1,61,1)
        if relief:
            cover=fuse('Frame_'+style+'_Relief',[cover]+relief)
            cover=cut('Frame_'+style+'_ThemeWindow',cover,window)
            cover=cut('Frame_'+style+'_ThemeReset',cover,reset_access)
        for i,(x,y) in enumerate(mounts[3:],4):
            boss=cyl('Frame_'+style+'_Boss'+str(i),x,y,6.3,2.1,10.3)
            expr(boss,'Height','Parameters.FrameTop - 6.3 mm')
            cover=fuse('Frame_'+style+'_Mount'+str(i),[cover,boss])
            cover=cut('Frame_'+style+'_Hole'+str(i),cover,cyl('Frame_'+style+'_Drill'+str(i),x,y,6.2,1.15,14))
            cb=cyl('Frame_'+style+'_Head'+str(i),x,y,14.9,1.85,5);expr(cb,'Placement.Base.z','Parameters.FrameTop - 1.7 mm')
            cover=cut('Frame_'+style+'_Counterbore'+str(i),cover,cb)
        cover.Label='Frame · '+label+' · variant'
        cover.addProperty('App::PropertyString','FrameStyle','Filo36');cover.FrameStyle=style
        cover.ViewObject.ShapeColor=(.16,.25,.23);styles[style]=cover
    active=doc.addObject('App::Link',prefix+'ActiveFrame');active.setLink(styles[configuration['frames'][side]['style']])
    done('electronics-lid',active,'Interchangeable frame · window and skirt','lid',tuple(int(configuration['frames'][side]['color'][i:i+2],16)/255 for i in (1,3,5)),True)

    print(side,'frame defined; recompute BEFORE meshes',flush=True)
    doc.recompute()
    print(side,'solid recompute complete',flush=True)
    # Keycaps remain the original KLP meshes; mirrored local Y is the KiCad/CAD
    # coordinate conversion, not a redesign of the keycap.
    keygroup=doc.addObject('App::DocumentObjectGroup',prefix+'Keys');keygroup.Label='Keycaps · Piantor centers and angles';assembly.addObject(keygroup)
    for key in layout['halves'][side]:
        choice=configuration['keycaps'][side][key['ref']];v=variants[choice['variant']]
        o=doc.addObject('Mesh::Feature',prefix+key['ref']); keygroup.addObject(o)
        mesh=Mesh.Mesh(str(ROOT/v['path'])); mat=A.Matrix();mat.A22=-1;mesh.transform(mat);mesh.flipNormals();o.Mesh=mesh
        o.Placement=A.Placement(A.Vector(key['x'],-key['y'],v['seating_z_mm']),A.Rotation(A.Vector(0,0,1),key['angle']+choice['rotation_deg']))
        o.Label='KLP '+key['ref'];o.ViewObject.ShapeColor=(.25,.55,.45) if key['row']==3 else (.91,.878,.783)
        for prop,value in [('KeycapVariant',v['id']),('KeyReference',key['ref']),('Side',side),('Source','KLP Lame / braindefender / CC-BY-SA-4.0 / unchanged mesh; nominal stem-tip datum')]:
            o.addProperty('App::PropertyString',prop,'Filo36');setattr(o,prop,value)
        o.addProperty('App::PropertyAngle','CapRotation','Filo36');o.CapRotation=choice['rotation_deg']
    print(side,'recomputing',flush=True)
    doc.recompute()
    print(side,'recomputed',flush=True)
    for o in history.Group:o.Visibility=False
    for o in finished:o.Visibility=True
    history.Visibility=False
    metadata['halves'][side]={'mount_holes':[[mx(x),y] for x,y in mounts], 'mount_tops_z':[7.6,7.6,7.6,14.9,14.9],
        'outer':profiles[side]['outer'],'pcb_outline':profiles[side]['pcb_outline'],
        'battery_opening':[mx(116.25) if side=='left' else mx(129.35),14.45,mx(129.35) if side=='left' else mx(116.25),46.95],
        'display_header':{'x':mx(122.8)-5.08,'y':50.8}, 'electronics_cover':profiles[side]['hood']}
    if side=='right':assembly.Placement.Base.x=161

doc.recompute()
G.activeDocument().activeView().viewTop();G.activeDocument().activeView().fitAll()
doc.saveAs(str(OUT/'Filo36.FCStd'))
(ROOT/'design/revH.json').write_text(json.dumps(metadata,indent=2)+'\n')
print('Saved native editable FreeCAD assembly:',OUT/'Filo36.FCStd',flush=True)
exec(compile((ROOT/'tools/freecad/export_revH.py').read_text(),str(ROOT/'tools/freecad/export_revH.py'),'exec'))
