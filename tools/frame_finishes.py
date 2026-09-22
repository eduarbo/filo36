"""Shared revH painted-face palette; no new geometry or print toolpaths.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import json
from pathlib import Path
FINISHES=json.loads((Path(__file__).resolve().parents[1]/'design/frame-finishes.json').read_text())

def role(style,side,x,y,height,roof=None):
    theme=FINISHES['styles'].get(style)
    if not theme or height<=(FINISHES['roof_mm'] if roof is None else roof)+1e-4:return 'body'
    if side=='right':x=160-x
    for zone in theme['zones']:
        x0,y0,x1,y1=zone['xy']
        if x0<=x<=x1 and y0<=y<=y1:return zone['role']
    return 'detail'

def palette(style,body=None):
    result=dict(FINISHES['styles'].get(style,{}).get('colors',{'body':'#304d4e'}))
    if body:result['body']=body
    return result

def rgb(color):return tuple(int(color[i:i+2],16)/255 for i in (1,3,5))
