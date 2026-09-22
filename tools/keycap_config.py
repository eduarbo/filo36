"""Pure-Python configuration checks shared by the build and FreeCAD macros.
Convex XY envelopes conservatively qualify configurations, not physical stem fit.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import copy, json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CATALOG=ROOT/'keycaps/catalog.json'

def polygon(hull,key,turn):
    a=math.radians(-key['angle']-turn);c,s=math.cos(a),math.sin(a)
    return [[key['x']+x*c-y*s,key['y']+x*s+y*c] for x,y in hull]

def gap(a,b):
    """Largest separating-axis clearance. A conservative Euclidean lower bound."""
    boxgap=max(min(x for x,y in b)-max(x for x,y in a),min(x for x,y in a)-max(x for x,y in b),min(y for x,y in b)-max(y for x,y in a),min(y for x,y in a)-max(y for x,y in b))
    if boxgap>=.2:return boxgap
    result=boxgap
    for p in (a,b):
        for u,v in zip(p,p[1:]+p[:1]):
            dx,dy=v[0]-u[0],v[1]-u[1];length=math.hypot(dx,dy)
            if length<1e-8:continue
            nx,ny=-dy/length,dx/length
            aa=[x*nx+y*ny for x,y in a];bb=[x*nx+y*ny for x,y in b]
            result=max(result,min(bb)-max(aa),min(aa)-max(bb))
    return result

def load():return json.loads(CATALOG.read_text())

def default_config(catalog=None):
    c=catalog or load();return copy.deepcopy(c['default_configuration'])

def check(config,catalog=None):
    c=catalog or load();variants={v['id']:v for v in c['variants']};errors=[];shapes={};minimum=float('inf')
    if config.get('schema')!='filo36-config-1' or config.get('revision')!='H':return ['Unsupported configuration format or revision.'],None
    if set(config.get('keycaps',{}))!={'left','right'} or set(config.get('frames',{}))!={'left','right'}:return ['Both halves are required.'],None
    for side,keys in c['layout'].items():
        if set(config['keycaps'][side])!={k['ref'] for k in keys}:return ['Missing keys or unknown positions.'],None
        f=config['frames'][side]
        if f.get('style') not in c['frame_styles']:errors.append('Unknown frame.')
        color=f.get('color','')
        if len(color)!=7 or color[0]!='#' or any(x not in '0123456789abcdefABCDEF' for x in color[1:]):errors.append('Invalid frame color.')
        shapes[side]={}
        for k in keys:
            x=config['keycaps'][side][k['ref']];v=variants.get(x.get('variant'));turn=x.get('rotation_deg')
            if not v or turn not in v['rotations_deg'] or not v['qualified_reference_positions']:
                errors.append(f"{side} {k['ref']}: unqualified variant or orientation.");continue
            p=polygon(v['hull_xy_mm'],k,turn);shapes[side][k['ref']]=p
            d=gap(p,c['frame_envelopes'][side]);minimum=min(minimum,d)
            if d<c['minimum_clearance_mm']-1e-7:errors.append(f"{side} {k['ref']}: violates the frame clearance.")
        for i,(ref,a) in enumerate(shapes[side].items()):
            for other,b in list(shapes[side].items())[i+1:]:
                d=gap(a,b);minimum=min(minimum,d)
                if d<c['minimum_clearance_mm']-1e-7:errors.append(f'{side} {ref}/{other}: insufficient keycap clearance.')
    return errors,round(minimum,6) if math.isfinite(minimum) else None

if __name__=='__main__':
    import sys
    cfg=json.loads(Path(sys.argv[1]).read_text()) if len(sys.argv)>1 else default_config()
    errors,minimum=check(cfg);print(json.dumps({'errors':errors,'conservative_clearance_mm':minimum},ensure_ascii=False))
    raise SystemExit(bool(errors))
