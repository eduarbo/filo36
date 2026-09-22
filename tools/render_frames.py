#!/usr/bin/env python3
"""Three actual revG frame exports, displayed separately for comparison.
SPDX-License-Identifier: GPL-3.0-or-later
"""
from pathlib import Path
import hashlib,json
import vtk
ROOT=Path(__file__).resolve().parents[1]
r=vtk.vtkRenderer();r.SetBackground(.929,.94,.918)
w=vtk.vtkRenderWindow();w.SetOffScreenRendering(1);w.SetSize(1500,900);w.SetMultiSamples(0);w.AddRenderer(r);r.SetUseFXAA(True)
sources=[]
for i,(style,color) in enumerate([('smooth',(.71,.69,.62)),('bevel',(.18,.36,.32)),('facet',(.62,.36,.23))]):
 p=ROOT/f'mechanical/revG/left-frame-{style}.stl';sources.append({'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 rd=vtk.vtkSTLReader();rd.SetFileName(str(p));rd.Update()
 n=vtk.vtkPolyDataNormals();n.SetInputConnection(rd.GetOutputPort());n.SetFeatureAngle(45);n.ConsistencyOn();n.AutoOrientNormalsOn();n.Update()
 mp=vtk.vtkPolyDataMapper();mp.SetInputConnection(n.GetOutputPort());a=vtk.vtkActor();a.SetMapper(mp);a.SetPosition(-111+40*i,0,0);a.GetProperty().SetColor(*color);r.AddActor(a)
 t=vtk.vtkTextActor();t.SetInput({'smooth':'SMOOTH','bevel':'BEVELED','facet':'FACETED'}[style]);t.SetPosition(210+430*i,170);t.GetTextProperty().SetFontSize(27);t.GetTextProperty().SetColor(.16,.25,.22);r.AddActor2D(t)
for text,y,size in [('FILO36 / INTERCHANGEABLE FRAMES',805,35),('Same mounts and inner cavity. Different upper profiles and colors.',755,22),('Actual revG CAD exports. Nominal study; printed fit and fastening untested.',55,20)]:
 t=vtk.vtkTextActor();t.SetInput(text);t.SetPosition(100,y);t.GetTextProperty().SetFontSize(size);t.GetTextProperty().SetColor(.16,.25,.22);r.AddActor2D(t)
c=r.GetActiveCamera();c.ParallelProjectionOn();c.SetFocalPoint(52,-37,8);c.SetPosition(52,-140,170);c.SetViewUp(0,0,1);c.SetParallelScale(53);r.ResetCameraClippingRange();w.Render()
f=vtk.vtkWindowToImageFilter();f.SetInput(w);f.ReadFrontBufferOff();f.Update();p=ROOT/'docs/images/revG-frames.png';writer=vtk.vtkPNGWriter();writer.SetFileName(str(p));writer.SetInputConnection(f.GetOutputPort());writer.Write();w.Finalize()
(ROOT/'validation/revG-frames-render.json').write_text(json.dumps({'image_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'sources':sources,'renderer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'geometry_changed':False},indent=2)+'\n')
