"""Bounded BREP equivalence: bijective solid pairs, never compound cross-cuts.

Drop-in shape_equivalence(expected, actual) for install_extra_frames snapshots.
Requires FreeCAD Part only when invoked. No document/file mutation or GUI use.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import itertools
import math

TOLERANCE = 1e-7


def _signature(shape):
    return {
        'shape_type': shape.ShapeType,
        'counts': {name: len(getattr(shape, name)) for name in
                   ('Solids', 'Shells', 'Faces', 'Wires', 'Edges', 'Vertexes')},
        'bounds_mm': [getattr(shape.BoundBox, name) for name in
                      ('XMin', 'YMin', 'ZMin', 'XMax', 'YMax', 'ZMax')],
        'volume_mm3': shape.Volume, 'area_mm2': shape.Area, 'length_mm': shape.Length,
        'vertices_mm': [(v.Point.x, v.Point.y, v.Point.z) for v in shape.Vertexes],
    }


def _vertex_distance(a, b):
    """Bidirectional nearest vertices, spatially indexed at the acceptance limit.

    If no vertex is within tolerance, infinity fails closed; accepted distances
    are exact nearest distances, without an O(n*n) scan of a large compound.
    """
    if not a and not b:
        return 0.0
    if not a or not b:
        return float('inf')
    def directional(points, candidates):
        cells = {}
        for p in candidates:
            key = tuple(math.floor(x / TOLERANCE) for x in p)
            cells.setdefault(key, []).append(p)
        maximum = 0.0
        for p in points:
            key = tuple(math.floor(x / TOLERANCE) for x in p)
            squared = float('inf')
            for offset in itertools.product((-1, 0, 1), repeat=3):
                near = tuple(k+d for k,d in zip(key, offset))
                for q in cells.get(near, ()):
                    squared = min(squared, sum((x-y)**2 for x,y in zip(p, q)))
            if squared > TOLERANCE**2:
                return float('inf')
            maximum = max(maximum, squared)
        return math.sqrt(maximum)
    return max(directional(a,b), directional(b,a))


def _metrics(a, b, vertices=True):
    if a['shape_type'] != b['shape_type'] or a['counts'] != b['counts']:
        raise ValueError('Shape type or topology counts changed')
    d = {
        'max_bounds_delta_mm': max(abs(x-y) for x,y in zip(a['bounds_mm'], b['bounds_mm'])),
        'volume_delta_mm3': abs(a['volume_mm3'] - b['volume_mm3']),
        'area_delta_mm2': abs(a['area_mm2'] - b['area_mm2']),
        'length_delta_mm': abs(a['length_mm'] - b['length_mm']),
    }
    if vertices:
        d['bidirectional_vertex_distance_mm'] = _vertex_distance(a['vertices_mm'], b['vertices_mm'])
    if any(not math.isfinite(x) or x > TOLERANCE for x in d.values()):
        raise ValueError(('Metrics or vertex differences exceed 1e-7', d))
    return d


def _full_solid_tree(shape):
    """Reject any free face/edge/vertex/shell instead of losing it in .Solids.

    A compound may contain nested compounds or compsolids, but every recursive
    leaf must be a Solid. Mixed-dimensional shapes use the original full check.
    """
    if shape.ShapeType == 'Solid':
        return True
    if shape.ShapeType not in ('Compound', 'CompSolid'):
        return False
    children = shape.childShapes()
    return bool(children) and all(_full_solid_tree(c) for c in children)


def _cuts(a, b):
    removed, added = a.cut(b), b.cut(a)
    result = {'before_minus_after_volume_mm3': removed.Volume,
              'after_minus_before_volume_mm3': added.Volume}
    if any(not math.isfinite(x) or x > TOLERANCE for x in result.values()):
        raise ValueError(('Symmetric difference exceeds 1e-7 mm3', result))
    return result, removed, added


def _bijection(signatures_a, signatures_b):
    """Maximum bipartite matching on metrics and complete vertex sets.

    Bounding boxes normally make each candidate unique. Duplicate equal solids
    are matched one-to-one; merely finding one neighbor per solid is insufficient.
    """
    candidates = []
    for sa in signatures_a:
        choices = []
        for j, sb in enumerate(signatures_b):
            try:
                _metrics(sa, sb, vertices=False)
                _metrics(sa, sb, vertices=True)
                choices.append(j)
            except ValueError:
                pass
        candidates.append(choices)
    assigned = {}
    def match(i, seen):
        for j in candidates[i]:
            if j in seen:
                continue
            seen.add(j)
            if j not in assigned or match(assigned[j], seen):
                assigned[j] = i
                return True
        return False
    for i in sorted(range(len(candidates)), key=lambda k: len(candidates[k])):
        if not match(i, set()):
            raise ValueError(('No bijection of solid geometry signatures', i, [len(c) for c in candidates]))
    if len(assigned) != len(signatures_a) or len(assigned) != len(signatures_b):
        raise ValueError('Solid matching was not bijective')
    return sorted((i,j) for j,i in assigned.items())


def shape_equivalence(expected, actual):
    """Same global 1e-7 geometric acceptance with linear many paired cuts.

    Expected/actual provide immutable _shape_brep strings and shape SHA-256s.
    Compound geometry is accepted only after every bijectively matched solid is
    equivalent, and SUMS of the residual volumes meet the original global limit.
    Non-solid leftovers trigger whole-shape checks instead of being discarded.
    """
    import Part
    a, b = Part.Shape(), Part.Shape()
    a.importBrepFromString(expected['_shape_brep'])
    b.importBrepFromString(actual['_shape_brep'])
    if not a.isValid() or not b.isValid():
        raise ValueError('Changed BREP contains an invalid shape')
    sa, sb = _signature(a), _signature(b)
    differences = _metrics(sa, sb)
    pairs = []
    if a.Solids and b.Solids and _full_solid_tree(a) and _full_solid_tree(b):
        solids_a, solids_b = list(a.Solids), list(b.Solids)
        sig_a, sig_b = list(map(_signature, solids_a)), list(map(_signature, solids_b))
        matching = _bijection(sig_a, sig_b)
        totals = dict(before_minus_after_volume_mm3=0.0, after_minus_before_volume_mm3=0.0)
        for i, j in matching:
            metrics = _metrics(sig_a[i], sig_b[j])
            residual, _, _ = _cuts(solids_a[i], solids_b[j])
            for key, value in residual.items():
                totals[key] += value
            pairs.append(dict(before_solid=i, after_solid=j, differences=dict(metrics, **residual)))
        if any(not math.isfinite(v) or v > TOLERANCE for v in totals.values()):
            raise ValueError(('Sum of paired residual volumes exceeds global 1e-7 mm3 limit', totals))
        differences.update(totals)
        method = 'bijective_solid_pairs_with_global_residual_bound'
    else:
        residual, removed, added = _cuts(a, b)
        differences.update(residual)
        # Mixed compounds can carry zero-volume free faces/wires even if they
        # also contain solids. Check residual area and length for EVERY fallback.
        differences['residual_area_mm2'] = removed.Area + added.Area
        differences['residual_length_mm'] = removed.Length + added.Length
        if any(not math.isfinite(v) or v > TOLERANCE for v in
               (differences['residual_area_mm2'], differences['residual_length_mm'])):
            raise ValueError(('Non-solid residual geometry differs', differences))
        method = 'whole_shape_fallback_including_nonsolid_residuals'
    return dict(status='hash_changed_but_geometrically_equivalent',
                before_brep_sha256=expected['shape'], after_brep_sha256=actual['shape'],
                byte_identity=expected['shape'] == actual['shape'],
                tolerance_mm=TOLERANCE, tolerance_mm2=TOLERANCE,
                tolerance_mm3=TOLERANCE, topology_counts=sa['counts'],
                method=method, differences=differences, solid_pairs=pairs)
