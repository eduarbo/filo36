#!/usr/bin/env python3
"""Check retained key geometry against pinned, unmodified Piantor sources.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import hashlib
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_sexpr(text):
    stack, top = [], []
    current = top
    for token in re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+', text):
        if token == '(':
            child = []
            current.append(child)
            stack.append(current)
            current = child
        elif token == ')':
            current = stack.pop()
        else:
            current.append(token.strip('"'))
    assert not stack
    return top[0]


def verify():
    layout = json.loads((ROOT / 'design/layout.json').read_text())
    manifest = json.loads((ROOT / 'sources/manifest.json').read_text())
    assert layout['units'] == 'mm'
    assert layout['source_commit'] == manifest['commit']
    for path, digest in manifest['files'].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, path
    for side, tx in [('left', -62), ('right', -47.24)]:
        board = read_sexpr((ROOT / f'sources/piantor/{side}.kicad_pcb').read_text())
        original = {}
        for node in board:
            if not isinstance(node, list) or node[0] != 'footprint':
                continue
            ref = next((x[2] for x in node if isinstance(x, list)
                        and x[:2] == ['fp_text', 'reference']), '')
            if re.fullmatch(r'K\d\d', ref):
                at = next(x for x in node if isinstance(x, list) and x[0] == 'at')
                original[ref] = (float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0)
        expected = set(original) - {'K00', 'K10', 'K20'}
        keys = layout['halves'][side]
        assert len(original) == 21 and len(keys) == 18
        assert {k['ref'] for k in keys} == expected
        for key in keys:
            x, y, angle = original[key['ref']]
            expected_values = {'source_x': x, 'source_y': y, 'x': x + tx, 'y': y - 41}
            for field, value in expected_values.items():
                assert math.isclose(key[field], value, abs_tol=1e-6), (side, key['ref'], field)
            assert math.isclose((key['angle'] - angle) % 360, 0, abs_tol=1e-6)
    print('PASS: 36 retained key centres and angles match the pinned Piantor sources.')


if __name__ == '__main__':
    verify()
