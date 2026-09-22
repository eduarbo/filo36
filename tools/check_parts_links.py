#!/usr/bin/env python3
"""Verify external parts-guide links without downloading/redistributing photos.
SPDX-License-Identifier: GPL-3.0-or-later
"""
from pathlib import Path
import concurrent.futures,json,re,urllib.request,urllib.error,hashlib,datetime
ROOT=Path(__file__).resolve().parents[1];doc=ROOT/'docs/parts.md';body=doc.read_text()
urls=sorted(set(re.findall(r'https://[^\s)\"<>]+',body)))
def read(url):
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Filo36 documentation link check'},method='HEAD')
        with urllib.request.urlopen(req,timeout=25) as r:return {'url':url,'status':r.status,'content_type':r.headers.get('Content-Type',''),'resolved_url':r.url}
    except Exception as e:return {'url':url,'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:rows=list(executor.map(read,urls))
report={'checked_at':datetime.date.today().isoformat(),'document_sha256':hashlib.sha256(doc.read_bytes()).hexdigest(),'photo_redistribution':False,'links':rows}
(ROOT/'validation/revI-parts-links.json').write_text(json.dumps(report,indent=2)+'\n')
for r in rows:print(r.get('status',r.get('error')),r['url'])
print('URL checks',len(rows),'errors',sum('error' in r for r in rows))
