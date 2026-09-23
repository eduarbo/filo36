"""Shared revH painted-face palette; no new geometry or print toolpaths.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import json
from pathlib import Path
FINISHES=json.loads((Path(__file__).resolve().parents[1]/'design/frame-finishes.json').read_text())

EXTENSIONS=json.loads((Path(__file__).resolve().parents[1]/'design/frame-extensions.json').read_text())
FINISHES['styles'].update({k:{f:v[f] for f in ['colors','labels','zones']} for k,v in EXTENSIONS['styles'].items()})

def role(style,side,x,y,height,roof=None):
    theme=FINISHES['styles'].get(style)
    if not theme or height<=(FINISHES['roof_mm'] if roof is None else roof)+1e-4:return 'body'
    if side=='right':x=160-x
    for zone in theme['zones']:
        x0,y0,x1,y1=zone['xy']
        if x0<=x<=x1 and y0<=y<=y1:return zone['role']
    return 'detail'

def palette(style,body=None,accents=None):
    result=dict(FINISHES['styles'].get(style,{}).get('colors',{'body':'#304d4e'}))
    if body:result['body']=body
    for name in ['detail','accent','secondary']:result[name]=(accents or {}).get(name,result.get(name,result['body']))
    return result

def rgb(color):return tuple(int(color[i:i+2],16)/255 for i in (1,3,5))
