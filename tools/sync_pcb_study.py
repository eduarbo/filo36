#!/usr/bin/env python3
"""Explicit revF placement reset, not a router. Refuses to erase routed work.

Uses the committed KiCad study as electrical source; native CAD owns the outline
and mechanical proposal. Ordinary editing uses KiCad/StepUp, not this reset tool.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import json
import sys
import re
import xml.etree.ElementTree as ET
from pathlib import Path
import pcbnew as p

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/'hardware/revF'
model=json.loads((ROOT/'design/revF.json').read_text())
layout=json.loads((ROOT/'design/layout.json').read_text())
mm=p.FromMM
v=lambda x,y:p.VECTOR2I(mm(x),mm(y))
left=p.LoadBoard(str(DIR/'filo36-left.kicad_pcb'))
netmap={(f.GetReference(),pad.GetNumber()):pad.GetNetname() for f in left.GetFootprints() for pad in f.Pads() if pad.GetNetname()}
left_j2=next(f for f in left.GetFootprints() if f.GetReference()=='J2')

def remove_root_items(text, names):
    """Strip only named direct board children; preserve quoted parentheses."""
    depth=0;quoted=False;escaped=False;start=None;cuts=[]
    for i,c in enumerate(text):
        if quoted:
            if escaped:escaped=False
            elif c=='\\':escaped=True
            elif c=='"':quoted=False
            continue
        if c=='"':quoted=True
        elif c=='(':
            depth+=1
            if depth==2:start=i
        elif c==')':
            if depth==2 and start is not None:
                tag=text[start+1:].split(None,1)[0].split(')',1)[0]
                if tag in names:cuts.append((start,i+1))
            depth-=1
    for a,b in reversed(cuts):text=text[:a]+text[b:]
    return text

all_drills={};report={};poses={}
for side in ['left','right']:
    path=DIR/f'filo36-{side}.kicad_pcb'; b=p.LoadBoard(str(path)); mx=lambda x:x if side=='left' else 160-x
    if len(b.GetTracks()) and '--initialize-unrouted' not in sys.argv:
        raise SystemExit('Routed board found. Preserve manual work; this placement reset requires an explicit --initialize-unrouted.')
    # KiCad 10.0.6's SWIG GetDrawings iterator is unavailable in the bundled
    # Python. Remove explicit top-level geometry from a disposable input copy.
    clean=remove_root_items(path.read_text(),{'segment','via','zone','gr_line','gr_arc','gr_circle','gr_text','gr_text_box','gr_rect','gr_poly','group'})
    scratch=ROOT/'build'/f'placement-{side}.kicad_pcb';scratch.parent.mkdir(exist_ok=True);scratch.write_text(clean)
    b=p.LoadBoard(str(scratch))
    fps={f.GetReference():f for f in b.GetFootprints()}
    if 'J2' not in fps:
        f=left_j2.Duplicate(False).Cast();b.Add(f);fps['J2']=f
    nets={n.GetNetname():n for n in b.GetNetsByNetcode().values()}
    for name in set(netmap.values()):
        if name not in nets:
            n=p.NETINFO_ITEM(b,name);b.Add(n);nets[name]=n
    xml=ET.parse(ROOT/'build'/f'{side}-netlist.xml').getroot()
    uuids={c.get('ref'):c.findtext('tstamps') for c in xml.findall('./components/comp')}
    root_uuid=re.search(r'\(uuid\s+"?([a-f0-9-]{36})',path.with_suffix('.kicad_sch').read_text())[1]
    for ref,f in fps.items():
        f.Models().clear()
        if ref in [k['ref'] for k in layout['halves'][side]]:
            key=next(k for k in layout['halves'][side] if k['ref']==ref)
            assert abs(p.ToMM(f.GetPosition().x)-key['x'])<.00001 and abs(p.ToMM(f.GetPosition().y)-key['y'])<.00001,(side,ref)
            assert abs(f.GetOrientationDegrees()-key['angle'])<.00001
            f.SetLocked(True)
        elif ref=='U1':f.SetOrientationDegrees(0);f.SetPosition(v(mx(122.8),17.3))
        elif ref=='J2':f.SetOrientationDegrees(0);f.SetPosition(v(mx(122.8)-5.08,50.8));f.SetValue('nice!view')
        elif ref=='J1':f.SetPosition(v(mx(115.8),55))
        elif ref=='SW1':f.SetOrientationDegrees(90 if side=='left' else -90);f.SetPosition(v(mx(132.5),57.65))
        elif ref=='SW2':f.SetPosition(v(mx(123),59.5))
        elif ref.startswith('H'):
            idx=int(ref[1:])-1; f.SetPosition(v(*model['halves'][side]['mount_holes'][idx]))
        for pad in f.Pads():
            name=netmap.get((ref,pad.GetNumber()),'')
            if name:pad.SetNet(nets[name])
            else:pad.SetNetCode(0)
        name={'U1':'mcu','J2':'display','J1':'jst','SW1':'slider','SW2':'reset'}.get(ref)
        if name or ref.startswith('K'):
            m=p.FP_3DMODEL();m.m_Filename='${KIPRJMOD}/models/'+(side+'-'+name if name else 'choc-envelope')+'.step'
            m.m_Scale=p.VECTOR3D(1,1,1);f.Models().push_back(m)
        f.Reference().SetVisible(False)
        if ref in uuids:
            f.SetPath(p.KIID_PATH('/'+root_uuid+'/'+uuids[ref]))
            f.SetSheetfile(f'filo36-{side}.kicad_sch');f.SetSheetname(f'filo36-{side}')
    contours=[model['halves'][side]['pcb_outline']]
    x0,y0,x1,y1=model['halves'][side]['battery_opening'];contours.append([(x0,y0),(x1,y0),(x1,y1),(x0,y1)])
    for contour in contours:
        for a,c in zip(contour,contour[1:]+contour[:1]):
            line=p.PCB_SHAPE();line.SetShape(p.SHAPE_T_SEGMENT);line.SetStart(v(*a));line.SetEnd(v(*c));line.SetLayer(p.Edge_Cuts);line.SetWidth(mm(.05));b.Add(line)
    text=p.PCB_TEXT(b);text.SetText('FILO36 revF - UNROUTED STUDY');text.SetPosition(v(70 if side=='left' else 90,64));text.SetTextSize(v(.8,.8));text.SetTextThickness(mm(.12));text.SetLayer(p.F_SilkS);b.Add(text)
    b.GetDesignSettings().SetGridOrigin(v(10,10));b.GetDesignSettings().SetBoardThickness(mm(1.6));b.BuildConnectivity();p.SaveBoard(str(path),b)
    drills=[]
    for f in b.GetFootprints():
        for pad in f.Pads():
            d=pad.GetDrillSize()
            if d.x:
                assert d.x==d.y,(f.GetReference(),'oval drill needs explicit native slot')
                drills.append({'ref':f.GetReference(),'pin':pad.GetNumber(),'x':p.ToMM(pad.GetPosition().x),'y':p.ToMM(pad.GetPosition().y),'radius':p.ToMM(d.x)/2})
    all_drills[side]=drills
    poses[side]={f.GetReference():{'x':p.ToMM(f.GetPosition().x),'y':p.ToMM(f.GetPosition().y),'angle':f.GetOrientationDegrees()} for f in b.GetFootprints()}
    report[side]={'footprints':len(fps),'tracks':len(b.GetTracks()),'holes':len(drills),'keys_locked':18,'electrical_state':'unrouted; no fabrication acceptance'}
(ROOT/'design/revF-drills.json').write_text(json.dumps(all_drills,indent=2)+'\n')
(ROOT/'design/revF-footprints.json').write_text(json.dumps(poses,indent=2)+'\n')
(ROOT/'validation/revF-pcb-placement.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
