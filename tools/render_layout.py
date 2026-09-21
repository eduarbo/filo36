#!/usr/bin/env python3
"""Generate the exact-layout diagram; this does not depict a final case.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import json
from pathlib import Path
from check_layout import verify

ROOT = Path(__file__).resolve().parents[1]
verify()
layout = json.loads((ROOT / 'design/layout.json').read_text())
svg = ['''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 640" role="img" aria-labelledby="title desc">
<title id="title">Filo36 — distribución de 36 teclas</title>
<desc id="desc">Dos mitades, cinco columnas de tres teclas y tres pulgares por mano. Posiciones y rotaciones procedentes de Piantor. Diagrama de layout, no carcasa final.</desc>
<rect width="1200" height="640" fill="#152c29"/>
<path d="M1100 0H1200V100Z" fill="#264b43"/>
<g font-family="Arial, Helvetica, sans-serif">
<text x="64" y="96" fill="#efe8d6" font-size="60" font-weight="700" letter-spacing="-2">FILO<tspan fill="#84cbb1">36</tspan></text>
<text x="64" y="137" fill="#b8c8be" font-size="20">Perfil bajo. Ángulos definidos.</text>
<text x="1136" y="89" text-anchor="end" fill="#84cbb1" font-size="14" letter-spacing="2">EN DESARROLLO</text>
</g>''']
for side in ('left', 'right'):
    offset = 0 if side == 'left' else 160
    for key in layout['halves'][side]:
        x = 90 + (offset + key['x']) * 3.2
        y = 227 + key['y'] * 3.2
        fill = '#84cbb1' if key['row'] == 3 else '#efe8d6'
        svg.append(f'<g transform="translate({x:.6f} {y:.6f}) rotate({-key["angle"]:.6f})" data-side="{side}" data-key="{key["ref"]}">')
        svg.append(f'<rect x="-27.2" y="-25.6" width="54.4" height="51.2" rx="4" fill="{fill}"/>')
        svg.append('<path d="M-20 17H20" stroke="#152c29" stroke-opacity=".12" stroke-width="2"/>')
        if key['ref'] == 'K14':
            svg.append('<circle r="2" cy="12" fill="#152c29" opacity=".5"/>')
        svg.append('</g>')
svg.append('''<path d="M64 584H1136" stroke="#38534a"/>
<g font-family="Arial, Helvetica, sans-serif" font-size="15" fill="#b8c8be">
<text x="64" y="613">3 × 5 + 3 por mano</text>
<text x="1136" y="613" text-anchor="end">Layout derivado de Piantor · No representa la carcasa final</text>
</g></svg>''')
path = ROOT / 'docs/images/layout.svg'
path.write_text('\n'.join(svg) + '\n')
print(f'Generated {path.relative_to(ROOT)}')
