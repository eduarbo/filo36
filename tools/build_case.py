#!/usr/bin/env python3
"""RevE mechanical study: actual case solids and nominal component envelopes.
SPDX-License-Identifier: GPL-3.0-or-later
No routed PCB, firmware, fit certification or manufacturing release is generated.
"""
import hashlib
import json
import struct
from pathlib import Path
import cadquery as cq
import vtk
from shapely.geometry import Polygon, box, Point
from shapely.affinity import rotate, translate
from source_outline import source_exterior
from check_layout import verify

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'mechanical/revE'
OUT.mkdir(parents=True, exist_ok=True)
verify()
layout = json.loads((ROOT / 'design/layout.json').read_text())
cap_bounds = {}
for cap in ['normal','normal_homing','thumb']:
    data=(ROOT / 'keycaps' / (cap+'.stl')).read_bytes()
    count=struct.unpack_from('<I',data,80)[0]
    assert len(data)==84+50*count
    points=[]
    for i in range(count):
        values=struct.unpack_from('<9f',data,84+i*50+12)
        points.extend([values[j:j+3] for j in [0,3,6]])
    cap_bounds[cap]=[min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)]
model = {'revision': 'E mechanical study', 'units': 'mm', 'manufacturing_ready': False,
         'bay_width': 24.0, 'previous_bay_width': 33.52, 'plate_top_z': 7.6,
         'electronics_top_z': 19.0, 'pcb_bottom_z': 3.8, 'pcb_top_z': 5.4,
         'battery_bottom_z': 6.2, 'battery_top_z': 10.0,
         'mcu_pcb_bottom_z': 11.0, 'mcu_envelope_top_z': 14.6,
         'display_pcb_bottom_z': 16.4, 'display_glass_top_z': 18.3,
         'halves': {}, 'parts': {}, 'pending': ['105 mm battery cable routing and bend radii',
         'routed PCB and connector footprints', 'detailed component dimensions and tolerances',
         'print fit, retention and service extraction', 'firmware integration, RF and measured power']}
report = {'scope': 'Nominal mechanical CAD, not hardware acceptance', 'halves': {}}


def prism(poly, z, height):
    assert poly.geom_type == 'Polygon' and not poly.interiors
    return cq.Workplane('XY').workplane(offset=z).polyline(list(poly.exterior.coords)[:-1]).close().extrude(height)


def cylinder(x, y, z, radius, height):
    return cq.Workplane('XY').workplane(offset=z).center(x, y).circle(radius).extrude(height)


def roof_height(y):
    if y < 13.2:
        return 14.8 + (y + 3.15) * (19.0 - 14.8) / (13.2 + 3.15)
    if y > 50.8:
        return 19.0 - (y - 50.8) * 8.0 / (68.5 - 50.8)
    return 19.0


def roof_volume(offset=0):
    # Sloping end roofs remove unused height; vertical roof thickness is 1.2 mm.
    profile=[(-20,5.0),(80,5.0),(80,11.0+offset),(68.5,11.0+offset),
             (50.8,19.0+offset),(13.2,19.0+offset),(-3.15,14.8+offset),(-20,14.8+offset)]
    return cq.Workplane('YZ').workplane(offset=-20).polyline(profile).close().extrude(200)


def save(shape, name, role, printable=False):
    solid = shape.val() if hasattr(shape, 'val') else shape
    assert solid.isValid(), name
    if printable:
        assert len(solid.Solids()) == 1, (name, len(solid.Solids()))
    for ext in (['stl', 'step'] if printable else ['stl']):
        path = OUT / f'{name}.{ext}'
        cq.exporters.export(solid, str(path), **({} if ext == 'step' else {'tolerance': .03, 'angularTolerance': .12}))
    b = solid.BoundingBox()
    if printable:
        reader = vtk.vtkSTLReader(); reader.SetFileName(str(OUT / f'{name}.stl')); reader.Update()
        edges = vtk.vtkFeatureEdges(); edges.SetInputData(reader.GetOutput())
        edges.BoundaryEdgesOn(); edges.NonManifoldEdgesOn(); edges.FeatureEdgesOff(); edges.ManifoldEdgesOff(); edges.Update()
        assert edges.GetOutput().GetNumberOfCells() == 0, (name, 'open or non-manifold mesh')
    model['parts'][name] = {'role': role, 'prototype_part': printable,
                           'mesh_closed_manifold': True if printable else None,
                           'bounds_mm': [b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax],
                           'stl_sha256': hashlib.sha256((OUT / f'{name}.stl').read_bytes()).hexdigest()}


for side, keys in layout['halves'].items():
    mx = lambda x: x if side == 'left' else 160-x
    bp = lambda a,b,c,d: box(a,b,c,d) if side == 'left' else box(160-c,b,160-a,d)
    src = source_exterior(ROOT / f'sources/piantor/{side}.kicad_pcb', -62 if side == 'left' else -47.24)
    src = src.intersection(box(19.2,-100,300,300) if side=='left' else box(-100,-100,140.8,300))
    hood = Polygon([(mx(x),y) for x,y in [(111,-3.15),(131,-3.15),(135,.85),(135,62),(128.5,68.5),(114,68.5),(111,65.5)]])
    key_outline = src.buffer(2.30,quad_segs=5).difference(bp(111,-30,200,68.5))
    outer = key_outline.union(hood).buffer(0)
    # Close enclosed seam pockets; preserve the complete concave exterior.
    outer = Polygon(outer.exterior.coords).simplify(.035,preserve_topology=True)
    assert outer.geom_type=='Polygon' and outer.is_valid
    inner = outer.buffer(-1.8,join_style='mitre')
    pcb = outer.buffer(-2.15,join_style='mitre')
    hood_inner = hood.buffer(-1.2,join_style='mitre')
    tray = prism(outer,0,6.3).cut(prism(inner,1.4,6.0))
    keyplate_poly = outer.difference(hood.buffer(.18,join_style='mitre'))
    assert keyplate_poly.geom_type=='Polygon', (side,keyplate_poly.geom_type)
    plate = prism(keyplate_poly,6.3,1.3)
    for key in keys:
        hole = rotate(box(key['x']-7,key['y']-7,key['x']+7,key['y']+7),-key['angle'],origin=(key['x'],key['y']))
        plate = plate.cut(prism(hole,5.8,2.5))
    lid = prism(hood,6.3,12.7).intersect(roof_volume())
    lid = lid.cut(prism(hood_inner,5.8,14).intersect(roof_volume(-1.2)))
    lid = lid.edges('>Z').chamfer(.25)
    usb_slot = prism(bp(116.3,-10,129.3,6.5),8.2,7.0)
    lid = lid.cut(usb_slot)
    power_slot = prism(bp(128.3,50.4,140,58.9),5.1,4.1)
    tray = tray.cut(power_slot);lid = lid.cut(power_slot)
    header_y = 48.4
    display_box = bp(115.7,header_y-34.8,129.9,header_y+1.4)
    lid = lid.cut(prism(display_box.buffer(.35,join_style='mitre'),15.2,5))
    mounts = [(mx(x),y) for x,y in [(21,37.5),(57,20.5),(41.2,66.6),(114.2,.6),(114.5,66.0)]]
    mount_tops=[]
    washers={}
    for i,(x,y) in enumerate(mounts):
        # Positive overlap joins the first pillar to the wall; tangency breaks its STL.
        radius = 2.5 if i==0 else (1.8 if i==1 else (2.1 if i>=3 else 2.3))
        tray = tray.union(cylinder(x,y,1.4,radius,2.4)).cut(cylinder(x,y,-.1,.85,4.2))
        washer = cylinder(x,y,5.4,radius,.9).cut(cylinder(x,y,5.3,1.15,1.1))
        # Removable spacer represented independently, not fused through the PCB.
        save(washer,f'{side}-washer-{i+1}','removable spacer',True)
        washers[f'washer-{i+1}']=washer
        target = lid if i>=3 else plate
        top = min(roof_height(y-1.85),roof_height(y+1.85)) if i>=3 else 7.6
        mount_tops.append(top)
        if i>=3:target = target.union(cylinder(x,y,6.3,radius,13.0).intersect(roof_volume()))
        target = target.cut(cylinder(x,y,5.8,1.15,14))
        target = target.cut(cq.Solid.makeCone(1.15,1.85,.7,cq.Vector(x,y,top-.7)))
        if i>=3:lid=target
        else:plate=target
    lid=lid.cut(cylinder(mx(115.8),60.8,8.0,1.5,12.0))
    # Narrow cuna between the two MCU socket rows; the USB is north of the cell.
    cradle = prism(bp(116.4,12.6,129.2,44.8),5.6,4.8).cut(prism(bp(116.8,13.0,128.8,44.4),6.2,5.0))
    cradle = cradle.cut(prism(bp(120.0,44.0,126.0,46.0),7.6,3))
    cell = prism(bp(117.05,13.2,128.55,44.2),6.2,3.8)
    riser = prism(bp(112.9,3.0,114.0,40.3),5.4,5.6).union(prism(bp(131.6,3.0,132.7,40.3),5.4,5.6))
    riser = riser.union(prism(bp(112.9,3.0,132.7,4.0),5.4,.8))
    mcu = prism(bp(113.3,4.3,132.3,40.3),11,1.0).union(prism(bp(115.3,11,130.3,34),12,2.6))
    usb = prism(bp(117.8,3.3,127.8,12),9.4,3.2)
    mcu = mcu.union(usb)
    sockets = [prism(bp(x-.9,8.53,x+.9,39.01),5.4,2.413) for x in [115.18,130.42]]
    # Five contacts are physically ordered left-to-right on BOTH commercial modules.
    header_x = mx(122.8)-5.08
    sled = prism(bp(115.4,header_y-2,130.2,header_y+2),5.4,11.0)
    sled = sled.cut(prism(bp(116.2,header_y-1.5,129.4,header_y+1.5),5.3,2.95))
    for i in range(5):sled = sled.cut(cylinder(header_x+2.54*i,header_y,5.2,.42,11.5))
    for bounds in [(115,header_y-35.3,116.3,header_y+2),(129.3,header_y-35.3,130.6,header_y+2),(115,header_y-35.3,130.6,header_y-34.3)]:
        sled = sled.union(prism(bp(*bounds),16.0,.4))
    for bounds in [(115,header_y-35.3,115.55,header_y+2),(130.05,header_y-35.3,130.6,header_y+2)]:
        sled = sled.union(prism(bp(*bounds),16.0,1.6))
    screen_board = prism(display_box,16.4,1.0)
    screen_glass = prism(bp(115.95,header_y-32.15,129.65,header_y-1.85),17.4,.9)
    screen_lower = prism(bp(116.8,header_y-25.15,128.8,header_y-6.15),15.4,1.0)
    screen = screen_board.union(screen_glass).union(screen_lower)
    jst = prism(bp(112.5,51.2,119.1,57.5),5.4,8.5)
    reset = prism(bp(112.8,57.8,118.8,63.8),5.4,2.5)
    slider = prism(bp(128.5,50.9,136.5,58.4),5.4,2.5)
    components={'battery':cell,'mcu':mcu,'display':screen,'jst':jst,'reset':reset,'slider':slider,
                'mcu-sockets':cq.Workplane('XY').newObject([cq.Compound.makeCompound([s.val() for s in sockets])])}
    service_parts={'cradle':cradle,'mcu-riser':riser,'display-sled':sled}
    case={'tray':tray,'key-plate':plate,'electronics-lid':lid}
    collisions={}
    for name,part in {**components,**service_parts}.items():
        overlaps={n:round(part.intersect(s).val().Volume(),6) for n,s in case.items()}
        collisions[name]=overlaps
        assert max(overlaps.values())<.001,(side,name,overlaps)
    pair_collisions={}
    all_components={**components,**service_parts}
    names=list(all_components)
    for i,a in enumerate(names):
        for b in names[i+1:]:
            vol=round(all_components[a].intersect(all_components[b]).val().Volume(),6)
            pair_collisions[a+' / '+b]=vol
            assert vol<.001,(side,a,b,vol)
    for a in ['tray','key-plate','electronics-lid']:
        for b in ['tray','key-plate','electronics-lid']:
            if a<b:assert case[a].intersect(case[b]).val().Volume()<.001,(a,b)
    for name,part in {**case,**service_parts}.items():save(part,side+'-'+name,name,True)
    for name,part in components.items():save(part,side+'-'+name,'nominal '+name)
    pcb_envelope=prism(pcb,3.8,1.6)
    save(pcb_envelope,side+'-pcb','unrouted PCB outline envelope')
    # Full assembly contains reference volumes. No fabrication source is implied.
    assembly=cq.Assembly()
    for name,part in {**case,**components,**service_parts,**washers,'pcb':pcb_envelope}.items():assembly.add(part,name=name)
    assembly.save(str(OUT/f'{side}-assembly.step'))
    cap_polygons=[]
    for k in keys:
        cap='thumb' if k['row']==3 else 'normal_homing' if k['ref']=='K14' else 'normal'
        cap_polygons.append(translate(rotate(box(*cap_bounds[cap]),-k['angle'],origin=(0,0)),k['x'],k['y']))
    key_clearance=min(hood.distance(p) for p in cap_polygons)
    assert key_clearance >= .2, (side,'nominal KLP to hood clearance',key_clearance)
    model['halves'][side]={'outer':list(outer.exterior.coords)[:-1],'pcb_outline':list(pcb.exterior.coords)[:-1],
                          'electronics_cover':list(hood.exterior.coords)[:-1],'mount_holes':mounts,'mount_tops_z':mount_tops,
                          'display_header':{'x':header_x,'y':header_y,'physical_orientation':'same on both halves'},
                          'size_mm':[outer.bounds[2]-outer.bounds[0],outer.bounds[3]-outer.bounds[1]],'keycap_footprint_clearance_mm':key_clearance}
    report['halves'][side]={'case_vs_components_mm3':collisions,'components_vs_components_mm3':pair_collisions,
                           'nominal_keycap_to_hood_gap_mm':key_clearance,'key_count':len(keys),
                           'body_height_mm':19,'plate_height_mm':7.6,'bay_width_mm':24,
                           'unmodeled':'battery cables, solder fillets, exact connectors, RF and physical tolerances'}
    print(side,'CAD parts valid; nominal envelope collisions zero;',model['halves'][side]['size_mm'],flush=True)
inputs=['tools/build_case.py','tools/source_outline.py','tools/check_layout.py','design/layout.json',
        'sources/manifest.json','sources/piantor/left.kicad_pcb','sources/piantor/right.kicad_pcb',
        'keycaps/normal.stl','keycaps/normal_homing.stl','keycaps/thumb.stl']
model['inputs']=[{'path':p,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()} for p in inputs]
(ROOT/'design/revE.json').write_text(json.dumps(model,indent=2)+'\n')
(ROOT/'validation/revE-mechanical.json').write_text(json.dumps(report,indent=2)+'\n')
