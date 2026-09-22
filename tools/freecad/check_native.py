"""Functional native-file edit/reopen test and portable component-model export.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import hashlib
import json
import sys
from pathlib import Path
import FreeCAD as A
import FreeCADGui as G
import Part
ROOT=Path(__file__).resolve().parents[2]
G.showMainWindow()
doc=A.openDocument(str(ROOT/'mechanical/revF/Filo36.FCStd'))
doc.recompute()
assert not any('FeaturePython' in o.TypeId for o in doc.Objects),'Custom proxy dependency'
parts={o.PartID:o for o in doc.Objects if hasattr(o,'PartID')}
baseline={k:(o.Shape.Volume,o.Shape.BoundBox.ZMax) for k,o in parts.items()}
params=doc.Parameters
aliases=json.loads((ROOT/'design/revF.json').read_text())['parameters']
params.set(aliases['FrameTop'],'17.2 mm');doc.recompute()
for side in ['left','right']:
    assert abs(parts[side+'-electronics-lid'].Shape.BoundBox.ZMax-17.2)<1e-6
    assert parts[side+'-electronics-lid'].Shape.Volume>baseline[side+'-electronics-lid'][0]
    assert abs(parts[side+'-tray'].Shape.Volume-baseline[side+'-tray'][0])<1e-6
copy=ROOT/'build/manual-edits/Filo36-my-variant.FCStd';copy.parent.mkdir(parents=True,exist_ok=True)
doc.saveAs(str(copy));A.closeDocument(doc.Name)
doc=A.openDocument(str(copy));doc.recompute();params=doc.Parameters
parts={o.PartID:o for o in doc.Objects if hasattr(o,'PartID')}
assert abs(parts['left-electronics-lid'].Shape.BoundBox.ZMax-17.2)<1e-6
assert all(o.Shape.isValid() for o in parts.values())
params.set(aliases['FrameTop'],'16.6 mm');doc.recompute()
before={s:parts[s+'-display'].Shape.BoundBox.YMin for s in ['left','right']}
params.set(aliases['DisplayShiftY'],'3.4 mm');doc.recompute()
for s in before:assert abs(parts[s+'-display'].Shape.BoundBox.YMin-before[s]+1)<1e-6
params.set(aliases['DisplayShiftY'],'2.4 mm');doc.recompute()
for k,o in parts.items():assert abs(o.Shape.Volume-baseline[k][0])<1e-5,(k,'restore failed')
doc.saveAs(str(ROOT/'build/manual-edits/Filo36-restored.FCStd'))

# Files are local to each footprint, with board-top Z=0, for ${KIPRJMOD} models.
poses=json.loads((ROOT/'design/revF-footprints.json').read_text())
out=ROOT/'hardware/revF/models';out.mkdir(exist_ok=True)
for side,prefix in [('left','L_'),('right','R_')]:
    half=doc.getObject(prefix+'Half');half.Placement=A.Placement();doc.recompute()
    for ref,name in {'U1':'mcu','J2':'display','J1':'jst','SW1':'slider','SW2':'reset'}.items():
        pose=poses[side][ref];shape=parts[side+'-'+name].Shape.copy()
        shape.translate(A.Vector(-pose['x'],pose['y'],-5.4))
        shape.rotate(A.Vector(),A.Vector(0,0,1),-pose['angle'])
        shape.exportStep(str(out/(side+'-'+name+'.step')))
choc=Part.makeBox(13.7,13.7,3.1,A.Vector(-6.85,-6.85,2.2)).fuse(Part.makeBox(9,5,1.3,A.Vector(-4.5,-2.5,5.2)))
choc.exportStep(str(out/'choc-envelope.step'))
receipt={'freecad_version':A.Version()[:3],'source_sha256':hashlib.sha256((ROOT/'mechanical/revF/Filo36.FCStd').read_bytes()).hexdigest(),
    'native_without_custom_proxies':True,'frame_height_edit_mm':[16.6,17.2],
    'save_close_reopen_preserves_edit':True,'screen_shift_mm':1,'restore_volumes_match':True,
    'component_models':'Relative KIPRJMOD STEP files; nominal envelopes, not manufacturer models',
    'keycap_count':len([o for o in doc.Objects if o.TypeId=='Mesh::Feature']),
    'models':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.step')}}
(ROOT/'validation/revF-native.json').write_text(json.dumps(receipt,indent=2)+'\n')
sys.__stdout__.write('PASS: native edit, save/reopen, restore and component-model export\n');sys.__stdout__.flush()
