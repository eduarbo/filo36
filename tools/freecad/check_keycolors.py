"""Verify individual cap colors and native frames survive configuration and FCStd roundtrip.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import sys,os,json,hashlib,traceback
from pathlib import Path
import FreeCAD as A
import FreeCADGui as G
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/freecad'))
from configuration import apply,extract
from frame_finishes import palette
OUT=ROOT/'build/keycolors';OUT.mkdir(parents=True,exist_ok=True)
source=Path(os.environ.get('FLAN36_COLOR_SOURCE',ROOT/'mechanical/revI/Flan36.FCStd'));digest=hashlib.sha256(source.read_bytes()).hexdigest()
result={}
try:
 G.showMainWindow();G.getMainWindow().hide();doc=A.openDocument(str(source));doc.recompute();cfg=extract(doc)
 index=0
 for side in ['left','right']:
  for key in cfg['keycaps'][side].values():
   index+=1;key['color']='#'+format((index*312709)%16777216,'06x')
 for side,style in [('left','mecha'),('right','kintsugi')]:
  p=palette(style);cfg['frames'][side]={'style':style,'color':p['body'],'accents':{k:p[k] for k in ['detail','accent','secondary']}}
 apply(doc,cfg)
 actual=extract(doc)
 assert actual==cfg,{'expected':cfg,'actual':actual}
 for prefix in ['L_','R_']:
  cover=doc.getObject(prefix+'ActiveFrame').LinkedObject
  actual={tuple(round(v*255) for v in c[:3]) for c in cover.ViewObject.DiffuseColor}
  assert len(actual)==4,(prefix,actual)
 target=OUT/'colors.FCStd';doc.saveAs(str(target));A.closeDocument(doc.Name);doc=A.openDocument(str(target));doc.recompute()
 assert extract(doc)==cfg,'Saved and reopened colors differ';A.closeDocument(doc.Name)
 assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
 result={'passed':True,'source_unchanged':True,'source_sha256':digest,'distinct_key_colors':36,'native_save_reopen_roundtrip':True,'frames':['mecha','kintsugi'],'physical_acceptance':False}
except Exception:result={'passed':False,'error':traceback.format_exc()}
(OUT/'freecad.json').write_text(json.dumps(result,indent=2)+'\n');sys.__stdout__.write(json.dumps(result)+'\n');sys.__stdout__.flush()
if os.environ.get('FILO_FREECAD_SUBPROCESS')=='1':os._exit(0 if result.get('passed') else 1)
