#!/usr/bin/env python3
"""Test catalog integrity, all qualified reference choices, presets and rejection.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import copy,hashlib,json,sys
from pathlib import Path
from keycap_config import ROOT,load,default_config,check,polygon,gap
c=load();assert len(c['variants'])==38
qualified=[v for v in c['variants'] if v['qualified_reference_positions']];assert len(qualified)==28
baseline=default_config(c);assert not check(baseline,c)[0]
checks=0
for v in c['variants']:
    assert hashlib.sha256((ROOT/v['path']).read_bytes()).hexdigest()==v['sha256']
    # The minimum of the entire mesh, including stems, remains above the plate
    # through a conservative 3.5 mm nominal travel study. Not measured seating.
    bottom=v['bounds_mm'][0][2]+v['seating_z_mm']-c['study_travel_mm']
    assert bottom>=c['plate_top_mm']+.59
    for choice in v['qualified_reference_positions']:
        cfg=copy.deepcopy(baseline);cfg['keycaps'][choice['side']][choice['key']]={'variant':v['id'],'rotation_deg':choice['rotation_deg']}
        errors,margin=check(cfg,c);assert not errors,(v['id'],choice,errors);checks+=1
presets={}
for p in (ROOT/'design/configurations').glob('*.json'):
    errors,margin=check(json.loads(p.read_text()),c);assert not errors,(p,errors);presets[p.stem]=margin
bad=copy.deepcopy(baseline);bad['keycaps']['left']['K01']={'variant':'choc_stem_mx_size_normal','rotation_deg':0};assert check(bad,c)[0]
bad=copy.deepcopy(baseline);bad['keycaps']['left']['K30']={'variant':'choc_stem_choc_size_normal_90deg','rotation_deg':0};assert check(bad,c)[0]
bad=copy.deepcopy(baseline);bad['keycaps']['left']['K30']={'variant':'choc_stem_choc_size_1.5u_normal','rotation_deg':0};assert check(bad,c)[0]
report={'catalog_variants':38,'variants_with_qualified_positions':28,'reference_choices_checked':checks,'presets_min_conservative_xy_clearance_mm':presets,'minimum_requested_clearance_mm':.2,
 'study_travel_mm':3.5,'minimum_pressed_mesh_z_mm':8.2,'plate_top_mm':7.6,'minimum_nominal_plate_gap_mm':.6,
 'scope':'Complete chosen combinations checked using unchanged STL convex XY envelopes. Non-overlap holds at rest and throughout independent vertical travel. Mesh below/above-plane bound checks plate. Does not validate switch internal travel or insertion/stem fit.',
 'rejections':['MX-size 1U on K01','90deg stem mesh with zero rotation','1.5U with no qualified position'],
 'layout_sha256':hashlib.sha256((ROOT/'design/layout.json').read_bytes()).hexdigest(),'catalog_sha256':hashlib.sha256((ROOT/'keycaps/catalog.json').read_bytes()).hexdigest(),
 'physical_acceptance':False}
(ROOT/'validation/revG-keycaps.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
