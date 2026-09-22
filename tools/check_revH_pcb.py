#!/usr/bin/env python3
"""KiCad readback of the new contour, preserving electrical and footprint state.
Run with KiCad's Python after CLI DRC into build/revH/drc-{side}.json.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import hashlib,json,re,collections
from pathlib import Path
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1]
def snapshot(path):
    board=p.LoadBoard(str(path));result={}
    assert len(board.GetTracks())==0
    for f in board.GetFootprints():
        result[f.GetReference()]={'xy':[f.GetPosition().x,f.GetPosition().y],'angle':f.GetOrientationDegrees(),'locked':f.IsLocked(),
            'symbol':f.GetPath().AsString(),'uuid':f.m_Uuid.AsString(),
            'pads':sorted((q.GetNumber(),q.GetPosition().x,q.GetPosition().y,q.GetNetname(),q.GetDrillSize().x,q.GetDrillSize().y) for q in f.Pads()),
            'models':[m.m_Filename for m in f.Models()]}
    return result
profiles=json.loads((ROOT/'design/revH-profiles.json').read_text())
layout=json.loads((ROOT/'design/layout.json').read_text())
report={'kicad_version':p.GetBuildVersion(),'fabrication_ready':False,'halves':{}}
pattern=r'\(gr_line\s+\(start\s+([\d.eE+-]+)\s+([\d.eE+-]+)\)\s+\(end\s+([\d.eE+-]+)\s+([\d.eE+-]+)\).*?\(layer\s+"?Edge.Cuts"?\)'
for side in ('left','right'):
    old=ROOT/f'hardware/revF/filo36-{side}.kicad_pcb';new=ROOT/f'hardware/revH/filo36-{side}.kicad_pcb'
    actual=snapshot(new);assert snapshot(old)==actual
    for key in layout['halves'][side]:
        f=actual[key['ref']];assert f['locked'] and abs(f['angle']-key['angle'])<1e-6
        assert all(abs(p.ToMM(f['xy'][i])-key[axis])<1e-6 for i,axis in enumerate(['x','y']))
    actual_edges=[]
    for m in re.finditer(pattern,new.read_text(),re.S):
        x,y,xx,yy=map(float,m.groups());actual_edges.append(tuple(sorted([(x,y),(xx,yy)])))
    x0,x1=(116.25,129.35) if side=='left' else (30.65,43.75)
    contours=[profiles[side]['pcb_outline'],[[x0,14.45],[x1,14.45],[x1,46.95],[x0,46.95]]]
    expected=[tuple(sorted(tuple(round(x,6) for x in p) for p in [a,b])) for poly in contours for a,b in zip(poly,poly[1:]+poly[:1])]
    assert sorted(actual_edges)==sorted(expected),'CAD and KiCad outline disagree'
    drc=json.loads((ROOT/f'build/revH/drc-{side}.json').read_text())
    counts=dict(collections.Counter(v['type'] for v in drc['violations']))
    assert not any('malformed' in k for k in counts),counts
    report['halves'][side]={'pcb_sha256':hashlib.sha256(new.read_bytes()).hexdigest(),'46_footprints_nets_drills_uuid_models_unchanged':len(actual)==46,
        'locked_original_keys':18,'outline_matches_cad_to_mm':.000001,'drc_violations':counts,'unconnected_items':len(drc['unconnected_items'])}
(ROOT/'validation/revH-electrical.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
