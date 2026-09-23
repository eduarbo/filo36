#!/usr/bin/env python3
"""Verify identity changes against the recorded pre-rename source, not altered history."""
from pathlib import Path
import hashlib,io,json,subprocess,zipfile,re,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from keycap_config import load,check,normalize
sha=lambda b:hashlib.sha256(b).hexdigest()
m=json.loads((ROOT/'validation/rebrand-file-map.json').read_text());results=[]
for e in m['renames']:
 old=subprocess.check_output(['git','show',m['baseline_commit']+':'+e['old_path']],cwd=ROOT);new=(ROOT/e['path']).read_bytes()
 assert sha(old)==e['old_sha256'] and sha(new)==e['sha256']
 if e['path'].endswith('.FCStd'):
  with zipfile.ZipFile(io.BytesIO(old)) as a,zipfile.ZipFile(io.BytesIO(new)) as b:
   assert a.namelist()==b.namelist()
   for name in a.namelist():
    data=a.read(name)
    if name in ['Document.xml','GuiDocument.xml']:data=data.replace(b'Filo36',b'Flan36').replace(b'filo36',b'flan36').replace(b'FILO36',b'FLAN36')
    assert data==b.read(name),name
 else:assert old.replace(b'filo36',b'flan36').replace(b'FILO36',b'FLAN36')==new
 results.append(e['path'])
fixtures=[load()['default_configuration'],*[json.loads(p.read_text()) for p in (ROOT/'design/configurations').glob('*.json')]]
for f in fixtures:
 before=dict(f,schema='filo36-config-1');after=dict(f,schema='flan36-config-1')
 assert not check(before)[0] and not check(after)[0]
 assert normalize(before)==normalize(after)
 assert normalize(before)['schema']=='flan36-config-1'
# Every current guide link resolves after native filename changes.
for p in [ROOT/'README.md',ROOT/'CONTRIBUTING.md',*(ROOT/'docs').glob('*.md')]:
 text=p.read_text();assert 'filo36' not in text.lower(),p
 for target in re.findall(r'\]\(([^)]+)\)',text):
  if target.startswith(('https:','http:','#','mailto:')):continue
  assert (p.parent/target.split('#')[0]).exists(),(p,target)
html=(ROOT/'docs/branding.html').read_text()
assert html.count('<img ')==1 and 'flan36-outline-black.svg' in html
assert not any(s in html for s in ['flan36-caramel-', 'flan36-split-', 'flan36-pixel-', 'flan36-outline-color', 'flan36-outline-white'])
report={'baseline_commit':m['baseline_commit'],'renamed_files':results,'native_zip_only_brand_metadata_changed':True,'pcb_only_brand_tokens_changed':True,'python_legacy_and_new_configurations_equal':len(fixtures),'current_guide_links_valid':True,'single_selected_logo':True}
(ROOT/'validation/rebrand-local.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: native ZIP invariants, PCB identity-only diff, legacy configs and current guide links')
