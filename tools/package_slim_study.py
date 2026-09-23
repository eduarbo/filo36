#!/usr/bin/env python3
"""Package complete recipe results without changing their measured outcomes.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import argparse,hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--reference',type=Path,required=True)
p.add_argument('--nominal',type=Path,required=True)
p.add_argument('--limit',type=Path,required=True)
p.add_argument('--source',type=Path,default=ROOT/'mechanical/revI/Flan36.FCStd')
p.add_argument('--out',type=Path,default=ROOT/'build/slim-mount-delivery')
a=p.parse_args();assert not a.out.exists(),'Use a new output directory'
styles=set(json.loads((ROOT/'keycaps/catalog.json').read_text())['frame_styles'])
batteries=set(json.loads((ROOT/'design/batteries.json').read_text())['profiles'])
recipes=[('reference-16p6',16.6,14.2,a.reference),('nominal-15p6',15.6,12.4,a.nominal),('limit-14p8',14.8,12.4,a.limit)]
report={'schema':'flan36-slim-study-delivery-1','source':str(a.source.resolve().relative_to(ROOT)),'source_sha256':sha(a.source),
 'physical_acceptance':False,'manufacturing_qualified':False,'execution':'Independently completed recipe partitions; identical study functions and source.',
 'candidates':{},'partitions':[],'artifacts':[]}
bridge_path=ROOT/'validation/revI-document-label.json'
if bridge_path.exists():
 bridge=json.loads(bridge_path.read_text())
 if report['source_sha256']==bridge['source_sha256']:
  assert bridge['passed'] and bridge['all_other_uncompressed_members_identical'] and bridge['label_normalized_xml_equal']
  published=ROOT/'mechanical/revI/Flan36.FCStd'
  assert sha(published)==bridge['output_sha256']
  report['installed_source']={'path':'mechanical/revI/Flan36.FCStd','sha256':sha(published),
   'identity_receipt':'validation/revI-document-label.json','identity_receipt_sha256':sha(bridge_path),
   'difference':'Only the root document Label was restored after the analyzed snapshot. Geometry and GUI member bytes are identical.'}
files={};common=None
for label,top,bottom,directory in recipes:
 path=directory/'report.json';r=json.loads(path.read_text())
 assert r['native_source_unchanged'] and r['inputs_unchanged']
 assert r['source_sha256']==report['source_sha256']
 if label!='reference-16p6':
  assert r['study_execution_complete']
  partition=r['execution_partition']
  assert partition['recipe']==label
  assert partition['runner']=='tools/freecad/study_slim_candidate.py'
  assert partition['runner_sha256']==sha(ROOT/partition['runner'])
 assert r['checker_sha256']==sha(ROOT/'tools/freecad/study_slim_mounts.py')
 identity={k:r[k] for k in ('source_parameters_mm','source_installed_shapes','checker_sha256','inputs','lift_samples_mm','freecad_version')}
 if common is None:common=identity
 else:assert identity==common,'Partitions used different sources, definitions or sampling'
 candidate=r['candidates'][label]
 assert candidate['frame_top_mm']==top and candidate['display_bottom_mm']==bottom
 assert set(candidate['halves'])=={'left','right'} and 'summary' in candidate
 for side,half in candidate['halves'].items():
  assert set(half['frames'])==styles and set(half['batteries'])==batteries
  assert all(half['unchanged_native_part_datums'].values())
  assert 'display_with_sled_lift_by_battery' in half['service']
  for frame in half['frames'].values():assert set(frame['batteries'])==batteries
  if label=='reference-16p6':
   for group in ('plate_options','base_saddle_options'):
    assert set(half['support_consolidation'][group])=={'solid','rim','terrace'}
 report['candidates'][label]=candidate
 report['partitions'].append({'recipe':label,'report_sha256':sha(path),'source_run_complete':bool(r.get('study_execution_complete')),
  'accepted_scope':'Both complete halves of this recipe only; no partial candidate is accepted.',
  'execution_partition':r.get('execution_partition')})
 selected=[item for item in r['artifacts'] if item['path'].startswith(label+'/') or label=='reference-16p6' and item['path'].startswith('support-consolidation/')]
 for item in selected:
  file=(directory/item['path']).resolve();assert file.is_relative_to(directory.resolve()) and sha(file)==item['sha256']
  assert item['path'] not in files;files[item['path']]=file;report['artifacts'].append(item)
 expected={f'{label}/{side}-{part}.{suffix}' for side in ('left','right') for part in [*('frame-'+s for s in styles),'display-sled','display','selected-solid-assembly'] for suffix in ('step','stl')}
 if label=='reference-16p6':
  for side,half in candidate['halves'].items():
   for group,part in [('plate_options','plate-with-washers'),('base_saddle_options','base-with-saddle')]:
    for style,result in half['support_consolidation'][group].items():
     if result['nominal_fusion_pass']:
      expected.update(f'support-consolidation/{side}-{style}-{part}.{suffix}' for suffix in ('step','stl'))
 assert {x['path'] for x in selected}==expected,'Incomplete or unexpected recipe/support exports'
report.update(common);report['study_execution_complete']=True
report['packager_sha256']=sha(Path(__file__))
a.out.mkdir(parents=True)
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
lines=['# Experimental slim parts','', '**Digital study only. Physical fit, electrical engagement, printing and retention remain unqualified.**','',
 '| Recipe | Plain roof / display bottom | Decorated frame top | Total native height with selected keycaps, excluding feet | Static checks | Service samples |',
 '|---|---:|---:|---:|---|---|']
for label,c in report['candidates'].items():
 frames=[f for h in c['halves'].values() for f in h['frames'].values()];heights=[b['actual_total_height_including_selected_meshes_mm'] for f in frames for b in f['batteries'].values()]
 lines.append(f"| {label} | {c['frame_top_mm']} / {c['display_bottom_mm']} mm | {max(f['actual_frame_top_mm'] for f in frames):g} mm | {min(heights):g}–{max(heights):g} mm | {'clear' if c['summary']['static_geometry_pass'] else 'interference'} | {'clear at samples' if c['summary']['service_samples_pass'] else 'findings; see report'} |")
lines += ['', 'Parts retain assembly coordinates. STEP assemblies contain solids; keycaps and switches are not included. Reference support-consolidation files are separate alternatives, not a replacement for the reference print kit. See the repository slim-mount guide for findings and limitations.', '', 'Every geometry file is listed with its SHA-256 in report.json. The report retains failed checks. No lower-stack option is approved for manufacturing.', '']
(a.out/'README.md').write_text('\n'.join(lines))
with zipfile.ZipFile(a.out/'slim-mounts.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for name,file in sorted(files.items()):z.write(file,name)
 for name in ('README.md','report.json'):z.write(a.out/name,name)
with zipfile.ZipFile(a.out/'slim-mounts.zip') as z:
 assert z.testzip() is None
 for item in report['artifacts']:assert hashlib.sha256(z.read(item['path'])).hexdigest()==item['sha256']
print('Verified complete partitions and',len(files),'geometry files:',a.out/'slim-mounts.zip')
