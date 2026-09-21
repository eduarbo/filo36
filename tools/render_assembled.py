#!/usr/bin/env python3
"""Render generated revE CAD and unchanged KLP meshes. No retouching or geometry edits.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import hashlib
import json
from pathlib import Path
import vtk

ROOT=Path(__file__).resolve().parents[1]
layout=json.loads((ROOT/'design/layout.json').read_text())
m=json.loads((ROOT/'design/revE.json').read_text())
used={};views={};IMAGE_DIR=ROOT/'docs/images';IMAGE_DIR.mkdir(exist_ok=True)


def render(kind):
    ren=vtk.vtkRenderer();ren.SetBackground(.929,.933,.918)
    win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.SetSize(2400,1500);win.SetMultiSamples(0);win.AddRenderer(ren)
    ren.SetUseFXAA(True)
    cache={}
    def mesh(path):
        if path not in cache:
            used[path]=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
            rd=vtk.vtkSTLReader();rd.SetFileName(str(ROOT/path));rd.Update()
            norms=vtk.vtkPolyDataNormals();norms.SetInputData(rd.GetOutput());norms.SetFeatureAngle(45);norms.ConsistencyOn();norms.AutoOrientNormalsOn();norms.Update()
            mp=vtk.vtkPolyDataMapper();mp.SetInputData(norms.GetOutput());cache[path]=mp
        return cache[path]
    def actor(mp,xyz,color,rz=0,rx=0,opacity=1):
        a=vtk.vtkActor();a.SetMapper(mp);a.RotateX(rx);a.RotateZ(rz);a.SetPosition(*xyz)
        p=a.GetProperty();p.SetColor(*color);p.SetAmbient(.20);p.SetDiffuse(.78);p.SetSpecular(.1);p.SetSpecularPower(32);p.SetInterpolationToPhong();p.SetOpacity(opacity);ren.AddActor(a);return a
    def part(side,name,color,dz=0,dx=0):
        return actor(mesh(f'mechanical/revE/{side}-{name}.stl'),(offset+dx,0,dz),color)
    def primitive(source,xyz,color,rz=0,rx=0):
        source.Update();mp=vtk.vtkPolyDataMapper();mp.SetInputConnection(source.GetOutputPort());return actor(mp,xyz,color,rz,rx)
    def cube(x,y,z,w,d,h,color,rz=0):
        s=vtk.vtkCubeSource();s.SetXLength(w);s.SetYLength(d);s.SetZLength(h);return primitive(s,(x,y,z),color,rz)
    def cylinder(x,y,z,r,h,color):
        s=vtk.vtkCylinderSource();s.SetRadius(r);s.SetHeight(h);s.SetResolution(36);return primitive(s,(x,y,z),color,rx=90)
    body=(.105,.145,.15);plate_color=(.145,.205,.207);cover=(.15,.215,.22)
    sides=['left'] if kind in ['side','stack'] else ['left','right']
    for side in sides:
        offset=0 if side=='left' else 161
        stack=kind=='stack';lid_dx=32 if stack else 0;lid_dz=13 if stack else 0
        part(side,'tray',body);part(side,'key-plate',plate_color)
        part(side,'electronics-lid',cover,lid_dz,lid_dx)
        part(side,'pcb',(.10,.32,.26))
        part(side,'cradle',(.30,.38,.39),10 if stack else 0)
        part(side,'battery',(.67,.70,.71),10 if stack else 0)
        part(side,'mcu-riser',(.26,.32,.33),25 if stack else 0)
        part(side,'mcu',(.07,.15,.16),25 if stack else 0)
        part(side,'mcu-sockets',(.05,.06,.062))
        part(side,'jst',(.88,.865,.815));part(side,'reset',(.25,.26,.27));part(side,'slider',(.16,.16,.17))
        part(side,'display-sled',(.25,.33,.34),45 if stack else 0)
        part(side,'display',(.055,.075,.073),45 if stack else 0)
        for i in range(1,6):part(side,f'washer-{i}',(.35,.37,.37))
        for i,(x,y) in enumerate(m['halves'][side]['mount_holes']):
            z=m['halves'][side]['mount_tops_z'][i]
            if stack and i>=3:continue
            cylinder(offset+x,y,z-.12,1.63,.20,(.09,.105,.11))
            cube(offset+x,y,z+.006,1.4,.22,.02,(.015,.02,.02))
        # Reflective screen artwork is illustrative, not a live hardware readback.
        cx=122.8 if side=='left' else 37.2;hy=m['halves'][side]['display_header']['y'];dz=45 if stack else 0
        glass=vtk.vtkPlaneSource();glass.SetOrigin(offset+cx-5.65,hy-30,18.315+dz);glass.SetPoint1(offset+cx+5.65,hy-30,18.315+dz);glass.SetPoint2(offset+cx-5.65,hy-4,18.315+dz)
        primitive(glass,(0,0,0),(.73,.79,.725))
        entries=[('BASE',hy-26,1.36),('BLE',hy-18,1.55),('L',hy-8,2.15)] if side=='left' else [('LINK',hy-26,1.36),('BAT',hy-18,1.55),('R',hy-8,2.15)]
        for text,y,scale in entries:
            src=vtk.vtkVectorText();src.SetText(text);src.Update();mp=vtk.vtkPolyDataMapper();mp.SetInputConnection(src.GetOutputPort())
            a=actor(mp,(offset+cx-4.75,y,18.34+dz),(.08,.15,.12),rx=180);a.SetScale(scale,scale,scale)
        for key in layout['halves'][side]:
            cube(offset+key['x'],key['y'],9.15,13.7,13.7,3.1,(.07,.095,.10),-key['angle'])
            # Nominal moving stem joins the housing to the cap's two stems.
            # This is an illustrative switch envelope, not a manufacturer CAD model.
            cube(offset+key['x'],key['y'],11.25,9.0,5.0,1.3,(.075,.10,.105),-key['angle'])
            cap='thumb' if key['row']==3 else 'normal_homing' if key['ref']=='K14' else 'normal'
            actor(mesh('keycaps/'+cap+'.stl'),(offset+key['x'],key['y'],12.2),(.25,.55,.45) if key['row']==3 else (.91,.878,.783),rz=-key['angle'])
        for x,y in [(26,26),(57,15),(41,64),(127,64)]:
            cylinder(offset+(x if side=='left' else 160-x),y,-.6,3,1.2,(.055,.067,.07))
    floor=vtk.vtkPlaneSource();floor.SetOrigin(-600,-600,-1.21);floor.SetPoint1(900,-600,-1.21);floor.SetPoint2(-600,800,-1.21)
    primitive(floor,(0,0,0),(.929,.933,.918))
    ren.AutomaticLightCreationOff()
    for pos,intensity in [((-80,15,350),.80),((390,150,220),.35),((160,-180,180),.30)]:
        light=vtk.vtkLight();light.SetLightTypeToSceneLight();light.SetPosition(*pos);light.SetFocalPoint(150,40,0);light.SetIntensity(intensity);ren.AddLight(light)
    # KiCad Y-down -> world coordinates, repairing handedness for normal lighting.
    actors=ren.GetActors();actors.InitTraversal()
    for _ in range(actors.GetNumberOfItems()):
        a=actors.GetNextActor();pose=vtk.vtkTransform();pose.Scale(1,-1,1);pose.Concatenate(a.GetMatrix())
        tf=vtk.vtkTransformPolyDataFilter();tf.SetTransform(pose);a.GetMapper().Update();tf.SetInputData(a.GetMapper().GetInput());tf.Update()
        rev=vtk.vtkReverseSense();rev.SetInputConnection(tf.GetOutputPort());rev.ReverseCellsOn();rev.ReverseNormalsOff();rev.Update()
        mp=vtk.vtkPolyDataMapper();mp.SetInputData(rev.GetOutput());a.SetMapper(mp);a.SetPosition(0,0,0);a.SetOrientation(0,0,0);a.SetScale(1,1,1)
    def label(text,x,y,size,color=(.14,.24,.22)):
        a=vtk.vtkTextActor();a.SetInput(text);a.SetPosition(x,y);p=a.GetTextProperty();p.SetFontFamilyToArial();p.SetFontSize(size);p.SetColor(*color);ren.AddActor2D(a)
    titles={'assembled':'FILO36  /  REV E','top':'FILO36  /  VISTA SUPERIOR','side':'FILO36  /  PERFIL LATERAL','stack':'FILO36  /  STACK DESMONTABLE'}
    label(titles[kind],105,1380,44)
    sub=('Mitad izquierda  /  KLP LAME  /  Perfil ortografico' if kind=='side' else '36 teclas  /  KLP LAME  /  Dos nice!view  /  Bahia de 24 mm') if kind!='stack' else 'Bateria debajo del micro; pantalla encima. Tapa de servicio independiente.'
    label(sub,108,1334,25,(.37,.44,.41))
    label('Estudio CAD revE. Cables, conectores definitivos, encaje y funcionamiento pendientes.',108,60,24,(.36,.42,.39))
    cam=ren.GetActiveCamera();cam.ParallelProjectionOn()
    if kind=='assembled':focal=(160,-44,7);pos=(182,-255,360);up=(0,0,1);scale=99
    elif kind=='top':focal=(160,-43,5);pos=(160,-43,450);up=(0,1,0);scale=99
    elif kind=='side':focal=(78,-38,8);pos=(350,-38,8);up=(0,0,1);scale=53
    else:focal=(88,-39,28);pos=(225,-270,205);up=(0,0,1);scale=70
    cam.SetFocalPoint(*focal);cam.SetPosition(*pos);cam.SetViewUp(*up);cam.SetParallelScale(scale);ren.ResetCameraClippingRange();win.Render()
    if kind=='side':
        label('Plate: 7.6 mm',105,1235,29);label('Cubierta electronica: 19 mm',105,1190,29)
        label('Alturas desde la base; las patas suman 1.2 mm. No se eleva toda la zona de teclas.',105,170,24,(.37,.44,.41))
    if kind=='stack':
        label('nice!view  /  nice!nano  /  LiPo 100 mAh',105,1230,27)
        label('Volumen de PCB sin ruteo',105,170,24,(.37,.44,.41))
    win.Render();f=vtk.vtkWindowToImageFilter();f.SetInput(win);f.SetInputBufferTypeToRGB();f.ReadFrontBufferOff();f.Update()
    writer=vtk.vtkPNGWriter();writer.SetFileName(str(IMAGE_DIR/f'revE-{kind}.png'));writer.SetInputConnection(f.GetOutputPort());writer.Write();win.Finalize()
    views[kind]={'keys':18*len(sides),'halves':sides,'exploded':kind=='stack','image_sha256':hashlib.sha256((IMAGE_DIR/f'revE-{kind}.png').read_bytes()).hexdigest()}
    print(kind,'rendered',flush=True)


for kind in ['assembled','top','side','stack']:render(kind)
receipt={'revision':'E','model_sha256':hashlib.sha256((ROOT/'design/revE.json').read_bytes()).hexdigest(),
         'layout_sha256':hashlib.sha256((ROOT/'design/layout.json').read_bytes()).hexdigest(),
         'renderer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         'meshes':[{'path':p,'sha256':h} for p,h in used.items()],
         'views':views,'geometry_source':'generated CAD, no image retouching',
         'illustrative':['component envelopes','switch bodies','screw heads','feet','screen artwork','unmeasured cap seating Z=12.2'],
         'unresolved':['battery cable routing','routed PCB','exact sockets and connectors','physical fit and tests']}
(ROOT/'validation/revE-render.json').write_text(json.dumps(receipt,indent=2)+'\n')
