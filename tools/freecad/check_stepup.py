"""Exercise the installed StepUp importer/exporter on disposable project copies.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
import FreeCAD as A
import FreeCADGui as G
import Part
import Sketcher

ROOT=Path(__file__).resolve().parents[2]
import faulthandler
faulthandler.enable(file=sys.__stderr__)
G.showMainWindow()
workbench=Path(os.environ.get('FILO_STEPUP_PATH',str(Path.home()/'Library/Application Support/FreeCAD/v1-1/Mod/kicadStepUpMod')))
sys.path.insert(0,str(workbench))
# The supported board loader handles current KiCad layers. The optional
# kicad_parser.makeBoard path still assumes historical numerical layer IDs.
sys.argv=[sys.argv[0]]
import kicadStepUptools as ksu
from fcad_parser import KicadPCB

scratch=ROOT/'build/stepup-portability'
shutil.copytree(ROOT/'hardware/revF',scratch,dirs_exist_ok=True)
os.environ['KIPRJMOD']=str(scratch)
report={'stepup_version':ksu.___ver___,'freecad_version':A.Version()[:3],'halves':{},'scope':'StepUp import and outline exchange on disposable copies; not fabrication acceptance'}
native=A.openDocument(str(ROOT/'mechanical/revF/Filo36.FCStd'))
references={o.PartID:o.Shape.copy() for o in native.Objects if hasattr(o,'PartID')}
A.closeDocument(native.Name)
pref=A.ParamGet('User parameter:BaseApp/Preferences/Mod/kicadStepUp')
old=pref.GetString('last_pcb_path')
# Session-only options mirror the documented GUI preferences; never save them.
ksu.show_messages=False;ksu.addVirtual=1;ksu.apply_edge_tolerance=False
ksu.aux_orig=0;ksu.grid_orig=1;ksu.base_orig=0;ksu.base_point=0;ksu.min_drill_size=0
try:
    for side in ['left','right']:
        path=scratch/f'filo36-{side}.kicad_pcb'
        ksu.onLoadBoard(str(path),True)
        doc=A.ActiveDocument;doc.recompute()
        board=next(o for o in doc.Objects if o.Name.startswith('Pcb_') and hasattr(o,'Shape'))
        shape=board.Shape.copy();zoffset=3.8-shape.BoundBox.ZMin;shape.translate(A.Vector(10,-10,zoffset))
        def clean(s):
            t=Part.Shape();t.importBrepFromString(s.exportBrepToString());return t
        shape=clean(shape);reference=clean(references[side+'-pcb'])
        delta=shape.cut(reference,1e-5).Volume+reference.cut(shape,1e-5).Volume
        assert delta<.05,(side,'native/StepUp PCB mismatch',delta)
        expected=[k['ref'] for k in json.loads((ROOT/'design/layout.json').read_text())['halves'][side]]+['U1','J2','J1','SW1','SW2']
        loaded={ref:next((o for o in doc.Objects if o.TypeId=='Part::Feature' and o.Label.startswith(ref+'_')),None) for ref in expected}
        assert all(loaded.values()),(side,'missing relative models',[k for k,v in loaded.items() if v is None])
        model_deltas={}
        for ref,part in {'U1':'mcu','J2':'display','J1':'jst','SW1':'slider','SW2':'reset'}.items():
            s=loaded[ref].Shape.copy();s.translate(A.Vector(10,-10,zoffset))
            r=clean(references[side+'-'+part]);s=clean(s)
            diff=s.cut(r,1e-5).Volume+r.cut(s,1e-5).Volume
            assert diff<.05,(side,ref,'model placement mismatch',diff)
            model_deltas[ref]=diff
        report['halves'][side]={'pcb_symmetric_difference_mm3':delta,'models_loaded':len(loaded),'model_placement_difference_mm3':model_deltas,
            'pcb_top_imported_mm':board.Shape.BoundBox.ZMax,'native_alignment_xyz_mm':[10,-10,zoffset],'models_from_moved_project':True}
        doc.saveAs(str(scratch/(side+'-import.FCStd')))
        A.closeDocument(doc.Name)
finally:pref.SetString('last_pcb_path',old)

# Pull exact Edge.Cuts into a native sketch, add a 0.5 mm offset to the internal
# opening's rear edge on a copy, and push through StepUp's own export operation.
side='left';path=scratch/'filo36-left.kicad_pcb'
pcb=KicadPCB.load(str(path)); doc=A.newDocument('StepUp_roundtrip')
sk=doc.addObject('Sketcher::SketchObject','PCB_Sketch');sk.Label='Edge.Cuts'
outline=[]
for edge in pcb.gr_line:
    if 'Edge.Cuts' not in str(edge.layer):continue
    a=list(map(float,edge.start));b=list(map(float,edge.end));outline.append((a,b))
    for pt in (a,b):
        if 116.0<pt[0]<130.0 and abs(pt[1]-46.95)<.0001:pt[1]+=.5
    sk.addGeometry(Part.LineSegment(A.Vector(a[0]-10,10-a[1],0),A.Vector(b[0]-10,10-b[1],0)),False)
doc.recompute()
G.Selection.clearSelection();G.Selection.addSelection(sk)
import kicadStepUptools as ksu
pref=A.ParamGet('User parameter:BaseApp/Preferences/Mod/kicadStepUp')
old=pref.GetString('last_pcb_path');old_origin=pref.GetInt('pcb_placement')
# Informational success dialog only: capture it in the test receipt. Warnings
# become errors; no geometry or exporter logic is replaced.
messages=[]
ksu.say_info=lambda msg:messages.append(msg)
def fail_warning(msg):raise RuntimeError(msg)
ksu.say_warning=fail_warning
try:
    pref.SetInt('pcb_placement',0)
    ksu.aux_orig=0;ksu.grid_orig=1
    ksu.export_pcb(str(path),'Edge.Cuts',sk.Name)
finally:
    pref.SetString('last_pcb_path',old);pref.SetInt('pcb_placement',old_origin)
doc.saveAs(str(scratch/'outline-example.FCStd'))
report['export_success_message_received']=any('new Edge pushed' in msg for msg in messages)
report['boolean_fuzzy_tolerance_mm']=1e-5
report['roundtrip_board']='build/stepup-portability/filo36-left.kicad_pcb'
report['roundtrip_expected_delta']='Battery opening rear edge +0.5 mm; footprints, net associations and other edges unchanged'
(ROOT/'build/stepup-import.json').write_text(json.dumps(report,indent=2)+'\n')
sys.__stdout__.write('StepUp import and export executed; PCB readback required\n');sys.__stdout__.flush()
# This standalone embedded-Python harness crashes during Qt/StepUp shutdown
# after all saves and assertions complete. Only its own subprocess may bypass
# that teardown. The application GUI and PCB readback are independent.
if os.environ.get('FILO_FREECAD_SUBPROCESS')=='1':
    os._exit(0)
