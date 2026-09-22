#!/usr/bin/env python3
"""Read StepUp's changed PCB with KiCad; verify only the requested opening edge moved.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import hashlib,json,re
from pathlib import Path
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'hardware/revF/filo36-left.kicad_pcb';edited=ROOT/'build/stepup-portability/filo36-left.kicad_pcb'
def snapshot(path):
    b=p.LoadBoard(str(path));result={}
    assert len(b.GetTracks())==0
    for f in b.GetFootprints():
        result[f.GetReference()]={'xy':[f.GetPosition().x,f.GetPosition().y],'angle':f.GetOrientationDegrees(),'locked':f.IsLocked(),
            'symbol':f.GetPath().AsString(),'uuid':f.m_Uuid.AsString(),
            'pads':sorted((q.GetNumber(),q.GetPosition().x,q.GetPosition().y,q.GetNetname(),q.GetDrillSize().x,q.GetDrillSize().y) for q in f.Pads()),
            'models':[m.m_Filename for m in f.Models()]}
    return result
assert snapshot(source)==snapshot(edited),'Footprint, net, drill, UUID or model changed'
pattern=r'\(gr_line\s+\(start\s+([\d.eE+-]+)\s+([\d.eE+-]+)\)\s+\(end\s+([\d.eE+-]+)\s+([\d.eE+-]+)\).*?\(layer\s+"?Edge.Cuts"?\)'
def edges(path,change=False):
    found=[]
    for m in re.finditer(pattern,path.read_text(),re.S):
        x,y,xx,yy=map(float,m.groups());pts=[[x,y],[xx,yy]]
        for pt in pts:
            if change and 116<pt[0]<130 and abs(pt[1]-46.95)<1e-5:pt[1]+=.5
        found.append(tuple(sorted(tuple(round(v,6) for v in pt) for pt in pts)))
    return sorted(found)
assert len(edges(source))==104
assert edges(source,True)==edges(edited),'Outline does not match the requested 0.5 mm change'
assert edges(source)!=edges(edited),'No geometric change'
report=json.loads((ROOT/'build/stepup-import.json').read_text())
report['roundtrip_verified']={'rear_edge_delta_mm':.5,'edge_segments':104,'footprints_and_nets_unchanged':True,'drills_and_models_unchanged':True,
    'only_requested_outline_delta':True,'source_pcb_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'edited_copy_sha256':hashlib.sha256(edited.read_bytes()).hexdigest()}
report['inputs']={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [ROOT/'mechanical/revF/Filo36.FCStd',ROOT/'tools/freecad/check_stepup.py',ROOT/'tools/check_stepup_readback.py',*(ROOT/'hardware/revF').glob('*.kicad_pcb')]}
(ROOT/'validation/revF-stepup.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: StepUp roundtrip read by KiCad; opening rear edge +0.5 mm; 46 footprints, nets, drills and other edges unchanged.')
