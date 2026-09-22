#!/usr/bin/env python3
"""Copy the unrouted reference and replace only its mechanical board outline.
No routing, net, footprint, rule or exclusion changes. Historical revF is read-only.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import json,re,shutil,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'hardware/revF';dest=ROOT/'hardware/revH'
if dest.exists():
    raise SystemExit('Refusing to overwrite existing revH PCB work. Preserve it first.')
shutil.copytree(source,dest)
profiles=json.loads((ROOT/'design/revH-profiles.json').read_text())
def root_children(text):
    depth=0;quoted=False;escaped=False;start=None
    for i,c in enumerate(text):
        if quoted:
            if escaped:escaped=False
            elif c=='\\':escaped=True
            elif c=='"':quoted=False
        elif c=='"':quoted=True
        elif c=='(':
            depth+=1
            if depth==2:start=i
        elif c==')':
            if depth==2:yield start,i+1,text[start:i+1]
            depth-=1
report={'scope':'Mechanical outline synchronization only; unrouted; no fabrication acceptance','halves':{}}
for side in ('left','right'):
    src=source/f'filo36-{side}.kicad_pcb';path=dest/src.name;text=src.read_text()
    children=list(root_children(text))
    assert not any(re.match(r'\((segment|via)\s',s) for a,b,s in children),'Routing found; preserve it'
    for a,b,s in reversed(children):
        if re.match(r'\(gr_',s) and '"Edge.Cuts"' in s:text=text[:a]+text[b:]
    text=text.replace('FILO36 revF - UNROUTED STUDY','FILO36 revH - UNROUTED STUDY')
    x0,x1=(116.25,129.35) if side=='left' else (30.65,43.75)
    outlines=[profiles[side]['pcb_outline'],[[x0,14.45],[x1,14.45],[x1,46.95],[x0,46.95]]]
    edges=[]
    for points in outlines:
        for a,b in zip(points,points[1:]+points[:1]):
            edges.append(f'(gr_line (start {a[0]:.6f} {a[1]:.6f}) (end {b[0]:.6f} {b[1]:.6f}) (stroke (width 0.05) (type default)) (layer "Edge.Cuts"))')
    at=text.rfind(')');text=text[:at]+'\n'+'\n'.join(edges)+'\n'+text[at:];path.write_text(text)
    before=[s for a,b,s in children if s.startswith('(footprint ')]
    after=[s for a,b,s in root_children(text) if s.startswith('(footprint ')]
    assert before==after,'Footprint content changed'
    report['halves'][side]={'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
        'pcb_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'footprints_byte_identical':len(before),
        'outline_segments':len(edges),'routing_changes':0}
(ROOT/'validation/revH-pcb-outline.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
