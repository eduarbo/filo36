#!/usr/bin/env python3
"""Reject stale revE renders and changed CAD inputs without regenerating anything.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def verify():
    model = json.loads((ROOT / 'design/revE.json').read_text())
    receipt = json.loads((ROOT / 'validation/revE-render.json').read_text())
    assert digest('design/revE.json') == receipt['model_sha256'], 'CAD metadata changed'
    assert digest('design/layout.json') == receipt['layout_sha256'], 'Layout changed'
    assert digest('tools/render_assembled.py') == receipt['renderer_sha256'], 'Renderer changed'
    for item in model['inputs']:
        assert digest(item['path']) == item['sha256'], f'Changed CAD source: {item["path"]}'
    for name, part in model['parts'].items():
        path = f'mechanical/revE/{name}.stl'
        assert digest(path) == part['stl_sha256'], f'Changed CAD mesh: {path}'
    for item in receipt['meshes']:
        assert digest(item['path']) == item['sha256'], f'Changed render input: {item["path"]}'
    for view, data in receipt['views'].items():
        assert digest(f'docs/images/revE-{view}.png') == data['image_sha256'], f'Stale image: {view}'
    readme = (ROOT / 'README.md').read_text()
    assert '](docs/images/revF-assembled.png)' in readme, 'Missing current hero'
    assert not (ROOT / 'docs/images/revD-assembled.png').exists(), 'Old hero restored'
    for path in [ROOT / 'README.md', *(ROOT / 'docs').glob('*.md')]:
        assert 'revD-assembled.png' not in path.read_text(), f'Old image linked: {path.name}'
    print('PASS: historical revE images and meshes preserved; README promotes revF.')


if __name__ == '__main__':
    verify()
