#!/usr/bin/env python3
"""Three actual themed revH frame exports, displayed separately for comparison.
SPDX-License-Identifier: GPL-3.0-or-later
"""
from pathlib import Path
import hashlib,json
import vtk
ROOT=Path(__file__).resolve().parents[1]
r=vtk.vtkRenderer();r.SetBackground(.929,.94,.918)
w=vtk.vtkRenderWindow();w.SetOffScreenRendering(1);w.SetSize(1500,900);w.SetMultiSamples(0);w.AddRenderer(r);r.SetUseFXAA(True)
sources=[]
for i,(style,color) in enumerate([('handheld',(.71,.69,.62)),('tv',(.18,.36,.32)),('cyberpunk',(.62,.36,.23))]):
 p=ROOT/f'mechanical/revH/left-frame-{style}.stl';sources.append({'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 rd=vtk.vtkSTLReader();rd.SetFileName(str(p));rd.Update()
 n=vtk.vtkPolyDataNormals();n.SetInputConnection(rd.GetOutputPort());n.SetFeatureAngle(45);n.ConsistencyOn();n.AutoOrientNormalsOn();n.Update()
 # Highlight actual raised geometry to make small relief legible. This is an
 # optional painted-face illustration, not a separate multi-material part.
 data=n.GetOutput();colors=vtk.vtkUnsignedCharArray();colors.SetNumberOfComponents(3);colors.SetName('Optional painted relief')
 for j in range(data.GetNumberOfPoints()):
  x,y,z=data.GetPoint(j)
  accent=(.23,.17,.20) if style=='handheld' else (.74,.64,.43) if style=='tv' else (.18,.66,.61)
  rgb=accent if z>16.65 else color
  colors.InsertNextTuple3(*(round(c*255) for c in rgb))
 data.GetPointData().SetScalars(colors)
 mp=vtk.vtkPolyDataMapper();mp.SetInputConnection(n.GetOutputPort());a=vtk.vtkActor();a.SetMapper(mp);a.SetPosition(-111+40*i,0,0);a.GetProperty().SetColor(*color);r.AddActor(a)
 t=vtk.vtkTextActor();t.SetInput({'handheld':'HANDHELD','tv':'RETRO TV','cyberpunk':'CYBERPUNK'}[style]);t.SetPosition(210+430*i,170);t.GetTextProperty().SetFontSize(27);t.GetTextProperty().SetColor(.16,.25,.22);r.AddActor2D(t)
for text,y,size in [('FILO36 / INTERCHANGEABLE FRAMES',805,35),('Three printable themes. Raised details shown with optional painted accents.',755,22),('Actual revH CAD exports. Nominal study; printed fit and fastening untested.',55,20)]:
 t=vtk.vtkTextActor();t.SetInput(text);t.SetPosition(100,y);t.GetTextProperty().SetFontSize(size);t.GetTextProperty().SetColor(.16,.25,.22);r.AddActor2D(t)
c=r.GetActiveCamera();c.ParallelProjectionOn();c.SetFocalPoint(52,-37,8);c.SetPosition(52,-140,170);c.SetViewUp(0,0,1);c.SetParallelScale(53);r.ResetCameraClippingRange();w.Render()
f=vtk.vtkWindowToImageFilter();f.SetInput(w);f.ReadFrontBufferOff();f.Update();p=ROOT/'docs/images/revH-frames.png';writer=vtk.vtkPNGWriter();writer.SetFileName(str(p));writer.SetInputConnection(f.GetOutputPort());writer.Write();w.Finalize()
(ROOT/'validation/revH-frames-render.json').write_text(json.dumps({'image_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'sources':sources,'renderer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'geometry_changed':False},indent=2)+'\n')
