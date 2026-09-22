#!/usr/bin/env python3
"""Orthographic measured-rim drawing from the native-verified design profiles.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from shapely.geometry import box
from shapely.affinity import rotate
R=Path(__file__).resolve().parents[1];profiles=json.loads((R/'design/revI-profiles.json').read_text());layout=json.loads((R/'design/layout.json').read_text())['halves']
W,H=1900,1130;im=Image.new('RGB',(W,H),'#f3f5ef');draw=ImageDraw.Draw(im)
fontpath=next((p for p in ['/System/Library/Fonts/Helvetica.ttc','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'] if Path(p).exists()),None)
font=lambda size:ImageFont.truetype(fontpath,size) if fontpath else ImageFont.load_default()
ink='#24413f';accent='#437f6c';scale=6
label=lambda x,y,s,size=25,color=ink:draw.text((x,y),s,font=font(size),fill=color)
label(80,50,'FILO36  /  A CONSISTENT RIM',43)
label(82,111,'4.75 mm on exposed straight faces. Original Piantor key centers and angles.',27)
for side,offset in [('left',65),('right',1010)]:
 def tx(q):return(offset+(q[0]-15)*scale,225+q[1]*scale)
 p=profiles[side];draw.polygon([tx(q) for q in p['outer']],fill='#345653')
 for k in layout[side]:
  cut=rotate(box(k['x']-7,k['y']-7,k['x']+7,k['y']+7),-k['angle'],origin=(k['x'],k['y']))
  draw.polygon([tx(q) for q in cut.exterior.coords],fill='#f3f5ef')
 draw.polygon([tx(q) for q in p['hood']],fill='#65817a')
 for m in json.loads((R/'design/revI-mounts.json').read_text())['left'][:3]:
  x,y=m['xy'];x=x if side=='left' else 160-x
  a,b=tx((x,y));draw.ellipse((a-6,b-6,a+6,b+6),fill='#172d2a')
 label(offset+20,187,side.upper(),19,'#71847d')
 if side=='left':
  def dim(a,b,text,pos):
   a,b=tx(a),tx(b);draw.line([a,b],fill='#ca8a43',width=3)
   for x,y in [a,b]:draw.ellipse((x-3,y-3,x+3,y+3),fill='#ca8a43')
   label(*pos,text,23)
  dim((66,5),(66,.25),'4.75',(310,200))
  dim((23,46),(18.25,46),'4.75',(5,488))
  dim((30,70),(30,74.75),'4.75',(140,690))
  k=next(k for k in layout['left'] if k['ref']=='K31');import math
  a=-math.radians(k['angle']);pt=lambda d:(k['x']-math.sin(a)*d,k['y']+math.cos(a)*d)
  dim(pt(7),pt(11.75),'4.75',(545,800))
label(80,878,'INTERNAL FASTENERS',23);label(80,917,'H1 moves between columns; the outline never depends on screws.',24)
label(1010,878,'EXACT MIRROR',23);label(1010,917,'One contour reflected across both halves. Bay stays 24 mm.',24)
label(80,994,'R0.8 corner blends and the bay / thumb bridge are explicit transitions.',24,'#62796e')
label(80,1042,'Native CAD checked. Printed fit and hardware operation remain untested.',22,'#62796e')
p=R/'docs/images/revI-rim.png';im.save(p)
report={'image_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'renderer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'profile_sha256':hashlib.sha256((R/'design/revI-profiles.json').read_bytes()).hexdigest(),'source':'Orthographic profile drawing; actual native-solid measurements in revI-rim-solids.json'}
(R/'validation/revI-rim-render.json').write_text(json.dumps(report,indent=2)+'\n')
print('Rendered measured rim / mirrored halves')
