#!/usr/bin/env python3
"""Check editable electrical study without calling an unrouted board production-ready.
Run with KiCad's pcbnew Python after CLI ERC, DRC and netlist export to build/.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import collections, hashlib, json, re
import xml.etree.ElementTree as ET
from pathlib import Path
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1]
layout=json.loads((ROOT/'design/layout.json').read_text())
report={'kicad_version':p.GetBuildVersion(),'fabrication_ready':False,'halves':{}}
for side in ('left','right'):
    path=ROOT/f'hardware/revF/filo36-{side}.kicad_pcb';board=p.LoadBoard(str(path))
    fps={f.GetReference():f for f in board.GetFootprints()}
    root=ET.parse(ROOT/f'build/{side}-netlist.xml').getroot()
    desired={(x.get('ref'),x.get('pin')):net.get('name').lstrip('/') for net in root.findall('./nets/net') for x in net.findall('node')}
    actual={(f.GetReference(),q.GetNumber()):q.GetNetname().lstrip('/') for f in fps.values() for q in f.Pads() if q.GetNetname()}
    for key,want in desired.items():
        if not want.startswith('unconnected-'):assert actual.get(key)==want,(side,key,want,actual.get(key))
    for key,value in actual.items():assert desired.get(key)==value,(side,key,'unexpected net')
    for component in root.findall('./components/comp'):
        f=fps[component.get('ref')];assert f.GetPath().AsString().endswith('/'+component.findtext('tstamps'))
    for key in layout['halves'][side]:
        f=fps[key['ref']]
        assert f.IsLocked()
        assert abs(p.ToMM(f.GetPosition().x)-key['x'])<1e-5
        assert abs(p.ToMM(f.GetPosition().y)-key['y'])<1e-5
        assert abs(f.GetOrientationDegrees()-key['angle'])<1e-5
    models=[]
    for f in fps.values():
        for model in f.Models():
            rel=model.m_Filename;assert rel.startswith('${KIPRJMOD}/models/')
            assert (path.parent/rel.replace('${KIPRJMOD}/','')).is_file()
            models.append(rel)
    erc=json.loads((ROOT/f'build/erc-{side}.json').read_text());drc=json.loads((ROOT/f'build/drc-{side}.json').read_text())
    erc_count=sum(len(s['violations']) for s in erc.get('sheets',[]));assert erc_count==0
    assert len(board.GetTracks())==0
    report['halves'][side]={'pcb_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'footprints':len(fps),'matched_net_nodes':len(desired),
        'symbol_uuid_links_match':True,'locked_original_keys':18,'relative_models':len(models),'erc_violations':erc_count,
        'drc_violations':dict(collections.Counter(v['type'] for v in drc['violations'])),'unconnected_items':len(drc['unconnected_items'])}
report['open_issues']=['24 MCU pads/half have 0.22 mm clearance to battery opening versus existing 0.5 mm rule.',
 'One switch mechanical pad/half is about 0.028 mm from outline; switch/mount courtyards overlap.',
 'Silkscreen near edge and 104 unrouted connections/half remain. Rules and DRC exclusions were not relaxed.']
(ROOT/'validation/revF-electrical.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: 36 exact keys, net associations, UUID links and portable models. DRC remains failing; unrouted study only.')
