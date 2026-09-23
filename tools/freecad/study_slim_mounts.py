"""Headless, read-only native study of Flan36 height and support consolidation.

Run: python3 tools/freecad/run_macos.py tools/freecad/study_slim_mounts.py
Optional FLAN36_STUDY_ROOT and FLAN36_STUDY_OUT override repository/output paths.
Writes only study STEP/STL, JSON and Markdown; never writes an FCStd document.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import hashlib
import itertools
import json
import os
from pathlib import Path
import re
import sys
import zipfile

import FreeCAD as A
import Part
import MeshPart

ROOT = Path(os.environ.get('FLAN36_STUDY_ROOT', Path(__file__).resolve().parents[2])).resolve()
OUT = Path(os.environ.get('FLAN36_STUDY_OUT', ROOT / 'build/slim-mount-study')).resolve()
SOURCE = Path(os.environ.get('FLAN36_STUDY_SOURCE', ROOT / 'mechanical/revI/Flan36.FCStd')).resolve()
EPS = 0.001  # Boolean reporting threshold in mm^3, NOT a fit tolerance.
GEOM_EPS = 1e-6  # Numerical comparison only, NOT a manufacturing allowance.
LIFTS = [0, .1, .2, .3, .5, .75, 1, 1.5, 2, 3, 4, 5, 6, 8, 10, 12, 16, 24]
CANDIDATES = [('reference-16p6', 16.6, 14.2), ('nominal-15p6', 15.6, 12.4),
              ('limit-14p8', 14.8, 12.4)]
INPUTS = ['design/revI-mounts.json', 'design/revI-magnets.json',
          'design/revI-wire-study.json', 'design/batteries.json',
          'tools/freecad/export_revI.py', 'tools/freecad/check_revI_service.py']


def log(*values):
    sys.__stdout__.write(' '.join(map(str, values)) + '\n')
    sys.__stdout__.flush()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bounds(shape):
    b = shape.BoundBox
    return [round(getattr(b, k), 6) for k in ('XMin', 'YMin', 'ZMin', 'XMax', 'YMax', 'ZMax')]


def signature(shape):
    return {'bounds_mm': bounds(shape), 'volume_mm3': round(shape.Volume, 6),
            'valid': shape.isValid(), 'solids': len(shape.Solids)}


def overlap(a, b):
    # Bounding boxes are conservative: omit only solids with no possible 3D
    # intersection. Keep one Boolean union/intersection so volumes are not
    # double-counted when a compound contains overlapping solids.
    def possible(x, y):
        return all(min(getattr(x, axis+'Max'), getattr(y, axis+'Max')) >
                   max(getattr(x, axis+'Min'), getattr(y, axis+'Min'))
                   for axis in ('X','Y','Z'))
    if not possible(a.BoundBox, b.BoundBox):return 0.0
    def solid_only(s):
        if s.ShapeType=='Solid':return True
        return s.ShapeType in ('Compound','CompSolid') and all(solid_only(c) for c in s.childShapes())
    if not solid_only(a) or not solid_only(b):return a.common(b).Volume
    aa, bb = a.Solids, b.Solids
    if not aa or not bb:return a.common(b).Volume
    ax, bx = [x.BoundBox for x in aa], [x.BoundBox for x in bb]
    pairs = [(i,j) for i,x in enumerate(ax) for j,y in enumerate(bx) if possible(x,y)]
    if not pairs:return 0.0
    ai, bi = sorted({i for i,j in pairs}), sorted({j for i,j in pairs})
    sa = aa[ai[0]] if len(ai)==1 else Part.makeCompound([aa[i] for i in ai])
    sb = bb[bi[0]] if len(bi)==1 else Part.makeCompound([bb[j] for j in bi])
    return sa.common(sb).Volume


def distance(a, b):
    return round(a.distToShape(b)[0], 6)


def numeric_equal(a, b):
    return abs(a - b) < GEOM_EPS


def require_shape(obj):
    if obj is None or not hasattr(obj, 'Shape') or obj.Shape.isNull() or not obj.Shape.isValid():
        raise ValueError('Missing/invalid native solid: ' + str(getattr(obj, 'Name', obj)))
    return obj.Shape.copy()


def variants(doc, prefix, prop):
    result = {}
    for obj in doc.Objects:
        if obj.Name.startswith(prefix) and obj.TypeId != 'App::Link' and hasattr(obj, prop):
            ident = str(getattr(obj, prop))
            if ident in result:
                raise ValueError('Duplicate native variant: ' + prefix + prop + ' ' + ident)
            result[ident] = obj
    if not result:
        raise ValueError('No native variants: ' + prefix + prop)
    return result


def thread_allowance(side, a, sa, b, sb, mounts):
    """Only the exact screw/tray tapped envelope used by export_revI is excluded."""
    screw = a if a.startswith('screw-') else b if b.startswith('screw-') else None
    if not screw or 'tray' not in (a, b):
        return 0.0
    spec = mounts['left'][int(screw.rsplit('-', 1)[1]) - 1]
    x, y = spec['xy']
    x = x if side == 'left' else 160 - x
    tip = spec['seat_z'] - spec['length']
    screw_shape = sa if a == screw else sb
    expected = [x - spec['head_diameter'] / 2, -y - spec['head_diameter'] / 2, tip,
                x + spec['head_diameter'] / 2, -y + spec['head_diameter'] / 2,
                spec['seat_z'] + spec['head_height']]
    if not all(numeric_equal(u, v) for u, v in zip(bounds(screw_shape), expected)):
        raise ValueError('Screw datum no longer matches explicit thread exclusion: ' + side + '-' + screw)
    thread = Part.makeCylinder(1, 3.8 - tip, A.Vector(x, -y, tip))
    return sa.common(sb).common(thread).Volume


def pair_checks(side, shapes, mounts):
    hits, excluded = [], []
    for (a, sa), (b, sb) in itertools.combinations(sorted(shapes.items()), 2):
        vol = overlap(sa, sb)
        if vol <= EPS:
            continue
        allowed = thread_allowance(side, a, sa, b, sb, mounts)
        item = {'a': a, 'b': b, 'volume_mm3': round(vol, 6),
                'excluded_tapped_thread_mm3': round(allowed, 6)}
        if vol - allowed > EPS:
            hits.append(item)
        elif allowed:
            excluded.append(item)
    return {'collisions': hits, 'explicit_thread_exclusions': excluded}


def collision_map(shape, others):
    result = {}
    for key, other in sorted(others.items()):
        vol = overlap(shape, other)
        if vol > EPS:
            result[key] = round(vol, 6)
    return result


def lift_checks(shape, obstacles):
    hits = []
    for dz in LIFTS:
        moved = shape.copy()
        moved.translate(A.Vector(0, 0, dz))
        for name, volume in collision_map(moved, obstacles).items():
            hits.append({'lift_mm': dz, 'part': name, 'volume_mm3': volume})
    return hits


def capture_probe(insert, host):
    results = {}
    for axis, xyz in [('x+', (1, 0, 0)), ('x-', (-1, 0, 0)), ('y+', (0, 1, 0)),
                      ('y-', (0, -1, 0)), ('z+', (0, 0, 1)), ('z-', (0, 0, -1))]:
        moved = insert.copy()
        moved.translate(A.Vector(*xyz).multiply(.3))
        results[axis] = round(overlap(moved, host), 6)
    return {'displacement_mm': .3, 'overlap_mm3': results,
            'all_six_directions_blocked_at_sample': min(results.values()) > EPS}


def export_shape(shape, path, report, connected=False):
    if not shape.isValid() or (connected and len(shape.Solids) != 1):
        raise ValueError('Invalid or disconnected export: ' + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    shape.exportStep(str(path.with_suffix('.step')))
    mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=.03, AngularDeflection=.12, Relative=False)
    if connected and not mesh.isSolid():
        raise ValueError('Open mesh: ' + str(path))
    mesh.write(str(path.with_suffix('.stl')))
    for suffix in ('.step', '.stl'):
        artifact = path.with_suffix(suffix)
        report['artifacts'].append({'path': str(artifact.relative_to(OUT)), 'sha256': sha(artifact),
                                    'manufacturing_qualified': False})


def fusion_check(host, additions):
    fused = host.copy()
    for shape in additions:
        fused = fused.fuse(shape)
    fused = fused.removeSplitter()
    original = Part.makeCompound([host] + additions)
    original_union_volume = host.Volume + sum(s.Volume for s in additions)
    # Inputs are expected to meet at faces. Explicitly account for any overlap.
    disjoint_inputs = all(overlap(a, b) <= EPS for a, b in itertools.combinations([host] + additions, 2))
    envelope_equal = all(numeric_equal(a, b) for a, b in zip(bounds(original), bounds(fused)))
    no_missing_volume = all(s.cut(fused).Volume <= EPS for s in [host] + additions)
    no_added_volume = fused.cut(original).Volume <= EPS
    item = {'valid': fused.isValid(), 'connected_solids': len(fused.Solids),
            'envelope_preserved': envelope_equal, 'no_material_added_or_removed': no_missing_volume and no_added_volume,
            'input_volumes_disjoint': disjoint_inputs,
            'volume_delta_mm3': round(fused.Volume - original_union_volume, 6),
            'original_combined_bounds_mm': bounds(original), 'fused_bounds_mm': bounds(fused),
            'assembly_height_delta_mm': round(fused.BoundBox.ZMax - original.BoundBox.ZMax, 6),
            'print_orientation_qualified': False, 'physical_retention_qualified': False}
    item['nominal_fusion_pass'] = all([item['valid'], len(fused.Solids) == 1,
                                     envelope_equal, item['no_material_added_or_removed']])
    return fused, item


def selected_mesh_bounds(doc, side, prefix):
    """Measure installed keycaps and linked switches; do not include hidden variants."""
    entries = {}
    for obj in doc.Objects:
        if getattr(obj, 'Side', None) == side and hasattr(obj, 'KeyReference') and hasattr(obj, 'Mesh'):
            # Mesh::Feature's Mesh carries its own Placement; halves are normalized.
            entries[obj.Name] = bounds(obj.Mesh)
        if obj.Name.startswith(prefix + 'Switch_') and obj.TypeId == 'App::Link':
            source = obj.LinkedObject
            for child in getattr(source, 'Group', []):
                if hasattr(child, 'Mesh'):
                    mesh = child.Mesh.copy()
                    mesh.transform(obj.LinkPlacement.toMatrix())
                    entries[obj.Name + '/' + child.Name] = bounds(mesh)
    if not entries:
        raise ValueError('Installed keycap/switch mesh height unavailable: ' + side)
    return entries


def support_consolidation(doc, side, prefix, shapes, report):
    washers = sorted(k for k in shapes if k.startswith('washer-'))
    if len(washers) != 3:
        raise ValueError('Expected three actual washers per half, found ' + str(washers))
    result = {'washers': {'count_per_half': len(washers), 'datums_mm': {k: bounds(shapes[k]) for k in washers}},
              'plate_options': {}, 'base_saddle_options': {}}
    for obj in doc.Objects:
        if not obj.Name.startswith(prefix) or obj.TypeId == 'App::Link' or not hasattr(obj, 'CaseStyle'):
            continue
        key = str(obj.CaseStyle)
        host = require_shape(obj)
        if obj.CaseGroup == 'plate':
            fused, item = fusion_check(host, [shapes[k] for k in washers])
            item['washer_top_meets_plate_bottom'] = all(numeric_equal(shapes[k].BoundBox.ZMax, host.BoundBox.ZMin) for k in washers)
            item['pcb_seat_preserved'] = all(numeric_equal(shapes[k].BoundBox.ZMin, float(doc.Parameters.PCBTop.Value)) for k in washers)
            item['loose_part_delta_per_half'] = -len(washers)
            item['datum_change_mm'] = 0
            item['nominal_fusion_pass'] &= item['washer_top_meets_plate_bottom'] and item['pcb_seat_preserved']
            obstacles = {k: s for k, s in shapes.items()
                         if k not in ('key-plate', 'electronics-lid')
                         and not k.startswith(('washer-', 'screw-', 'frame-target-'))}
            item['sampled_fused_plate_lift_collisions'] = lift_checks(fused, obstacles)
            item['plate_removal_assumption'] = 'Frame, all screws and keycaps removed; switch meshes are excluded from collision acceptance. Soldered-switch/plate removal is not qualified.'
            result['plate_options'][key] = item
            if item['nominal_fusion_pass']:
                export_shape(fused, OUT / 'support-consolidation' / (side + '-' + key + '-plate-with-washers'), report, True)
        elif obj.CaseGroup == 'base':
            fused, item = fusion_check(host, [shapes['cradle']])
            item['loose_part_delta_per_half'] = -1
            item['datum_change_mm'] = 0
            item['optional'] = True
            item['caveat'] = 'A fused saddle cannot be replaced independently; underside/cavity printing and battery insulation remain unqualified.'
            result['base_saddle_options'][key] = item
            if item['nominal_fusion_pass']:
                export_shape(fused, OUT / 'support-consolidation' / (side + '-' + key + '-base-with-saddle'), report, True)
    if not result['plate_options'] or not result['base_saddle_options']:
        raise ValueError('Case variants missing; cannot verify support consolidation.')
    return result


def common_service(doc, side, prefix, shapes, batteries, mounts):
    result = {}
    cage = shapes['battery-retainer'].copy()
    cage.translate(A.Vector(0, 0, .2))
    result['cage_capture'] = {'lift_mm': .2, 'pcb_overlap_mm3': round(overlap(cage, shapes['pcb']), 6),
                              'requires_pcb_removal': overlap(cage, shapes['pcb']) > EPS}
    cavity = require_shape(doc.getObject(prefix + 'CradleCavity')).BoundBox
    roof_bottom = require_shape(doc.getObject(prefix + 'KeeperA')).BoundBox.ZMin
    motion = Part.makeBox(cavity.XLength, cavity.YLength, roof_bottom - cavity.ZMin,
                          A.Vector(cavity.XMin, cavity.YMin, cavity.ZMin))
    result['cell_translation_bound'] = {'bounds_mm': bounds(motion),
        'source': 'Actual native CradleCavity XY and KeeperA underside; conservative box, not a swelling allowance.',
        'lead_intersections_mm3': collision_map(motion, {k: s for k, s in shapes.items() if k.startswith('battery-lead-')})}
    driver_hits = []
    for spec in mounts['left']:
        x, y = spec['xy']
        x = x if side == 'left' else 160 - x
        driver = Part.makeCylinder(1.5, 25, A.Vector(x, -y, spec['seat_z'] + spec['head_height']))
        for name, shape in shapes.items():
            if name == 'electronics-lid' or name.startswith(('frame-target-', 'screw-')):
                continue
            if spec['id'] in ('H4', 'H5') and (name == 'key-plate' or name.startswith('washer-')):
                continue
            vol = overlap(driver, shape)
            if vol > EPS:
                driver_hits.append({'mount': spec['id'], 'part': name, 'volume_mm3': round(vol, 6)})
    result['nominal_3mm_driver_shaft'] = {'collisions': driver_hits,
        'sequence': 'Remove caps and frame; remove the plate after H1-H3 before accessing H4-H5. Tool handle and real driver are unqualified.'}
    result['base_insert_pockets'] = {k: capture_probe(s, shapes['tray']) for k, s in shapes.items() if k.startswith('magnet-')}
    result['pcb_lift_by_battery'] = {}
    for ident, battery in batteries.items():
        fixed = {k: s for k, s in shapes.items() if k in ('tray', 'battery-retainer', 'cradle') or k.startswith('magnet-')}
        fixed['battery'] = battery
        result['pcb_lift_by_battery'][ident] = lift_checks(shapes['pcb'], fixed)
    result['pcb_lift_assumption'] = 'Plate, screws and modules removed first; samples do not establish unplugging, soldered-switch service or a continuous path.'
    display_pair = Part.makeCompound([shapes['display'], shapes['display-sled']])
    excluded = {'electronics-lid', 'display', 'display-sled'}
    obstacles = {k: s for k, s in shapes.items() if k not in excluded and not k.startswith('frame-target-')}
    # All cells fit below this moving display assembly, but still evaluate both.
    result['display_with_sled_lift_by_battery'] = {}
    for ident, battery in batteries.items():
        obstacles['battery'] = battery
        result['display_with_sled_lift_by_battery'][ident] = lift_checks(display_pair, obstacles)
    result['display_lift_assumption'] = 'Frame removed; display plus sled move together. Contacts are not modeled as qualified connectors; unplugging force is unverified.'
    return result


def study_side(doc, side, prefix, mounts, report, label):
    objects = [o for o in doc.Objects if str(getattr(o, 'PartID', '')).startswith(side + '-')]
    shapes = {o.PartID[len(side) + 1:]: require_shape(o) for o in objects}
    for required in ('tray', 'pcb', 'key-plate', 'battery', 'battery-retainer', 'cradle',
                     'display', 'display-sled', 'mcu', 'mcu-riser', 'mcu-sockets', 'jst', 'electronics-lid'):
        if required not in shapes:
            raise ValueError('Required component missing: ' + side + '-' + required)
    frames = {k: require_shape(o) for k, o in variants(doc, prefix, 'FrameStyle').items()}
    batteries = {k: require_shape(o) for k, o in variants(doc, prefix, 'BatteryStyle').items()}
    expected_batteries = set(json.loads((ROOT / 'design/batteries.json').read_text())['profiles'])
    if set(batteries) != expected_batteries or len(batteries) < 2:
        raise ValueError('Native battery variants do not match current catalog: ' + side)
    meshes = selected_mesh_bounds(doc, side, prefix)
    mesh_zmin = min(b[2] for b in meshes.values())
    mesh_zmax = max(b[5] for b in meshes.values())
    frame_top, frame_roof = float(doc.Parameters.FrameTop.Value), float(doc.Parameters.FrameRoof.Value)
    result = {'parts': {k: signature(s) for k, s in shapes.items()}, 'installed_mesh_bounds_mm': meshes,
              'selected_battery': str(doc.getObject(prefix + 'ActiveBattery').LinkedObject.BatteryStyle),
              'selected_frame': str(doc.getObject(prefix + 'ActiveFrame').LinkedObject.FrameStyle),
              'display_cover_installed_in_source': bool(doc.getObject(prefix + 'Half').DisplayCoverInstalled),
              'modeled_component_pairs': pair_checks(side, shapes, mounts), 'batteries': {}, 'frames': {}}
    permitted_changed_parts = {'electronics-lid', 'display', 'display-sled'}
    result['unchanged_native_part_datums'] = {
        k: signature(s) == report['source_installed_shapes'][side + '-' + k]
        for k, s in shapes.items() if k not in permitted_changed_parts}
    if not all(result['unchanged_native_part_datums'].values()):
        raise ValueError('Recipe moved or changed an undeclared native component: ' + side)
    for ident, battery in batteries.items():
        fixed = {k: s for k, s in shapes.items() if k not in ('battery', 'electronics-lid')}
        result['batteries'][ident] = {'shape': signature(battery), 'component_collisions_mm3': collision_map(battery, fixed),
                                      'mcu_vertical_gap_mm': round(shapes['mcu'].BoundBox.ZMin - battery.BoundBox.ZMax, 6)}
    result['clearances_mm'] = {'mcu_to_display_shape_distance': distance(shapes['mcu'], shapes['display']),
        'jst_to_nominal_roof_underside': round(frame_top - frame_roof - shapes['jst'].BoundBox.ZMax, 6),
        'mcu_socket_top_to_pcb_bottom_z': round(shapes['mcu'].BoundBox.ZMin - shapes['mcu-sockets'].BoundBox.ZMax, 6)}
    result['electrical_datum_qualification'] = {'qualified': False,
        'reason': 'Distance between solids is mechanical clearance only. Actual mating header lengths, pin engagement, contact ordering, socket retention and electrical continuity are not established by this study.',
        'display_bottom_changed_from_source_mm': round(float(doc.Parameters.DisplayBottom.Value) - report['source_parameters_mm']['DisplayBottom'], 6)}
    targets = {k: s for k, s in shapes.items() if k.startswith('frame-target-')}
    no_frame = {k: s for k, s in shapes.items() if k != 'electronics-lid'}
    static = {k: s for k, s in no_frame.items() if not k.startswith('frame-target-')}
    px = 116.8 if side == 'left' else 160 - 128.8
    usb = Part.makeBox(12, 20, 5, A.Vector(px, -18.8, 6.7))
    for style, frame in sorted(frames.items()):
        log('Frame',label,side,style)
        fixed = {k: s for k, s in no_frame.items() if k != 'battery'}
        common_hits = collision_map(frame, fixed)
        moving = Part.makeCompound([frame] + list(targets.values()))
        fi = {'shape': signature(frame), 'nominal_roof_top_mm': frame_top,
              'nominal_roof_underside_mm': round(frame_top - frame_roof, 6),
              'actual_frame_top_mm': round(frame.BoundBox.ZMax, 6),
              'relief_above_nominal_roof_mm': round(frame.BoundBox.ZMax - frame_top, 6),
              'component_collisions_mm3': common_hits,
              'usb_nominal_plug_corridor_collision_mm3': round(overlap(frame, usb), 6),
              'target_pockets': {k: capture_probe(s, frame) for k, s in targets.items()}, 'batteries': {}}
        for ident, battery in sorted(batteries.items()):
            obstacles = dict(static, battery=battery)
            installed = [frame, battery] + [s for k, s in no_frame.items() if k != 'battery']
            compound = Part.makeCompound(installed)
            zmin = min(compound.BoundBox.ZMin, mesh_zmin)
            zmax = max(compound.BoundBox.ZMax, mesh_zmax)
            fi['batteries'][ident] = {'frame_collision_mm3': round(overlap(frame, battery), 6),
                'frame_plus_targets_lift_collisions': lift_checks(moving, obstacles),
                'solid_assembly_zmin_mm': round(compound.BoundBox.ZMin, 6),
                'solid_assembly_zmax_mm': round(compound.BoundBox.ZMax, 6),
                'actual_total_zmin_mm': round(zmin, 6), 'actual_total_zmax_mm': round(zmax, 6),
                'actual_total_height_including_selected_meshes_mm': round(zmax - zmin, 6)}
        result['frames'][style] = fi
        export_shape(frame, OUT / label / (side + '-frame-' + re.sub(r'[^a-zA-Z0-9_-]', '_', style)), report, True)
    log('Service',label,side)
    result['service'] = common_service(doc, side, prefix, shapes, batteries, mounts)
    for name in ('display-sled', 'display'):
        export_shape(shapes[name], OUT / label / (side + '-' + name), report, name == 'display-sled')
    export_shape(Part.makeCompound(list(shapes.values())), OUT / label / (side + '-selected-solid-assembly'), report)
    if label == 'reference-16p6':
        log('Support consolidation',side)
        result['support_consolidation'] = support_consolidation(doc, side, prefix, shapes, report)
    return result


def summarize(candidate):
    metrics = {'unexpected_component_pair_collisions': 0, 'battery_component_collisions': 0,
               'frame_component_collisions': 0, 'usb_corridor_collisions': 0,
               'sampled_frame_lift_collisions': 0, 'failed_target_capture_probes': 0,
               'driver_collisions': 0, 'pcb_lift_collisions': 0, 'display_lift_collisions': 0,
               'cell_motion_lead_collisions': 0, 'failed_cage_capture_probes': 0,
               'failed_base_capture_probes': 0}
    for side in candidate['halves'].values():
        metrics['unexpected_component_pair_collisions'] += len(side['modeled_component_pairs']['collisions'])
        metrics['battery_component_collisions'] += sum(len(b['component_collisions_mm3']) for b in side['batteries'].values())
        for frame in side['frames'].values():
            metrics['frame_component_collisions'] += len(frame['component_collisions_mm3'])
            metrics['usb_corridor_collisions'] += int(frame['usb_nominal_plug_corridor_collision_mm3'] > EPS)
            metrics['failed_target_capture_probes'] += sum(not p['all_six_directions_blocked_at_sample'] for p in frame['target_pockets'].values())
            for battery in frame['batteries'].values():
                metrics['frame_component_collisions'] += int(battery['frame_collision_mm3'] > EPS)
                metrics['sampled_frame_lift_collisions'] += len(battery['frame_plus_targets_lift_collisions'])
        service = side['service']
        metrics['driver_collisions'] += len(service['nominal_3mm_driver_shaft']['collisions'])
        metrics['pcb_lift_collisions'] += sum(map(len, service['pcb_lift_by_battery'].values()))
        metrics['display_lift_collisions'] += sum(map(len, service['display_with_sled_lift_by_battery'].values()))
        metrics['cell_motion_lead_collisions'] += len(service['cell_translation_bound']['lead_intersections_mm3'])
        metrics['failed_cage_capture_probes'] += int(not service['cage_capture']['requires_pcb_removal'])
        metrics['failed_base_capture_probes'] += sum(not p['all_six_directions_blocked_at_sample'] for p in service['base_insert_pockets'].values())
    metrics['static_geometry_pass'] = not any(metrics[k] for k in
        ('unexpected_component_pair_collisions', 'battery_component_collisions', 'frame_component_collisions', 'usb_corridor_collisions'))
    metrics['service_samples_pass'] = not any(metrics[k] for k in
        ('sampled_frame_lift_collisions', 'failed_target_capture_probes', 'driver_collisions',
         'pcb_lift_collisions', 'display_lift_collisions', 'cell_motion_lead_collisions',
         'failed_cage_capture_probes', 'failed_base_capture_probes'))
    metrics['nominal_checks_pass'] = metrics['static_geometry_pass'] and metrics['service_samples_pass']
    return metrics


def markdown(report):
    lines = ['# Flan36 slim support study', '',
             '**Nominal CAD study. No manufacturing, print-orientation, electrical-contact or physical-retention qualification.**', '',
             'Source SHA-256: `' + report['source_sha256'] + '`. The native source was not saved or replaced.', '',
             '| Recipe | Roof / display bottom (mm) | Frame tops (mm) | Total modeled height with selected caps (mm) | Nominal checks |',
             '|---|---:|---:|---:|---|']
    for label, candidate in report['candidates'].items():
        frames = [f for s in candidate['halves'].values() for f in s['frames'].values()]
        heights = [b['actual_total_height_including_selected_meshes_mm'] for f in frames for b in f['batteries'].values()]
        tops = [f['actual_frame_top_mm'] for f in frames]
        status = 'clear at checked samples' if candidate['summary']['nominal_checks_pass'] else 'interference / failed check; see JSON'
        lines.append('| {} | {} / {} | {}–{} | {}–{} | {} |'.format(label, candidate['frame_top_mm'], candidate['display_bottom_mm'], min(tops), max(tops), min(heights), max(heights), status))
    lines += ['', 'Roof height is not keyboard height. Raised decoration, displays, switches and the selected keycaps are measured separately from the roof parameter.', '',
              '| Support decision | Loose parts, both halves | Assembly height change | Constraint |',
              '|---|---:|---:|---|',
              '| Fuse the three washers into each plate | −6 if all recorded fusion checks pass | 0 mm | Preserve actual washer seats and plate datum; inspect STEP/STL before a print trial. |',
              '| Optionally fuse each insulating saddle into its base | −2 if all recorded fusion checks pass | 0 mm | Saddle loses independent replacement; printing and insulation remain unqualified. |',
              '| Keep battery cages | 0 | 0 mm | Cage feet remain captured by the PCB; removal requires PCB removal. |',
              '| Keep MCU risers and display sleds | 0 | 0 mm from part removal | No verified replacement for their load path, alignment and insulation. |',
              '| Keep magnets, pins and pockets | 0 | 0 mm | Six-direction geometric probes do not prove magnetic hold, peel strength or cycling. |', '',
              'The 15.6 / 12.4 mm recipe is an experimental candidate only. The 14.8 mm recipe is a limiting comparison; inspect JST/roof interference in the report. Do not adopt a lowered display solely from an empty collision list.', '',
              'Both halves, every native FrameStyle and both catalogued battery bodies are evaluated. Reports include wire volumes, frame-plus-pin lifts, PCB and display/sled lifts, 3 mm driver shafts, USB corridor and insert-pocket probes. Lift paths are sampled, not continuous sweeps; plug removal, real wire ends, bending forces and actual tools remain open.', '',
              'Only the existing exporter\'s exact tapped M2 screw/tray volume is excluded from collision failures. Other penetrations are reported. Surface contact or separation does not establish electrical engagement, manufacturing tolerance or retention.', '',
              'The JSON contains per-part datums, per-style fusion connected-solid results, all failed checks and artifact hashes. Study files preserve the source shape coordinates; orient and qualify them separately before printing.', '',
              'Reproduce with `python3 tools/freecad/run_macos.py tools/freecad/study_slim_mounts.py`. The default output is `build/slim-mount-study`; override `FLAN36_STUDY_OUT` for a separate destination. No FCStd is saved, so its GUI document and custom appearance cannot be stripped by this headless study.', '']
    return '\n'.join(lines)


def main():
    if A.GuiUp:
        raise RuntimeError('Run this study headlessly; it must not control an interactive FreeCAD session.')
    if A.listDocuments():
        raise RuntimeError('Use a fresh headless process with no pre-opened documents.')
    if OUT == SOURCE.parent or SOURCE.parent in OUT.parents:
        raise ValueError('Study output must be outside the reference mechanical/revI directory.')
    if OUT.exists() and any(OUT.iterdir()):
        raise ValueError('Use an empty study output directory to avoid mixing runs: ' + str(OUT))
    OUT.mkdir(parents=True, exist_ok=True)
    mounts = json.loads((ROOT / 'design/revI-mounts.json').read_text())
    report = {'schema': 'flan36-slim-mount-study-1', 'source': str(SOURCE.relative_to(ROOT)),
              'source_sha256': sha(SOURCE), 'checker_sha256': sha(__file__),
              'inputs': {p: sha(ROOT / p) for p in INPUTS}, 'headless': not A.GuiUp,
              'freecad_version': list(A.Version()[:3]), 'boolean_volume_reporting_threshold_mm3': EPS,
              'lift_samples_mm': LIFTS, 'physical_acceptance': False, 'manufacturing_qualified': False,
              'scope': 'Actual native solids; both halves, both battery profiles, every discovered FrameStyle. Installed keycap/switch meshes supply height only, not solid collision acceptance.',
              'artifacts': [], 'candidates': {}}
    with zipfile.ZipFile(SOURCE) as archive:
        gui_entries = [n for n in archive.namelist() if 'GuiDocument' in n]
        report['source_gui_document_sha256'] = {n: hashlib.sha256(archive.read(n)).hexdigest() for n in gui_entries}
    doc = A.openDocument(str(SOURCE))
    try:
        for prefix in ('L_', 'R_'):
            doc.getObject(prefix + 'Half').Placement = A.Placement()
        doc.recompute()
        report['source_parameters_mm'] = {alias: float(getattr(doc.Parameters, alias).Value) for alias in
            ('FrameTop', 'FrameRoof', 'DisplayBottom', 'MCUBottom', 'PlateBottom', 'PCBTop', 'BatteryBottom')}
        report['source_installed_shapes'] = {o.PartID: signature(require_shape(o)) for o in doc.Objects if hasattr(o, 'PartID')}
        for label, top, display_bottom in CANDIDATES:
            log('Studying', label, 'roof', top, 'display', display_bottom)
            for alias, value in [('FrameTop', top), ('DisplayBottom', display_bottom)]:
                doc.Parameters.set(doc.Parameters.getCellFromAlias(alias), str(value) + ' mm')
            doc.recompute()
            if not numeric_equal(float(doc.Parameters.FrameTop.Value), top) or not numeric_equal(float(doc.Parameters.DisplayBottom.Value), display_bottom):
                raise ValueError('Parameter aliases did not recompute to the requested recipe.')
            candidate = {'frame_top_mm': top, 'display_bottom_mm': display_bottom, 'halves': {}}
            for side, prefix in [('left', 'L_'), ('right', 'R_')]:
                log('Checking', label, side)
                candidate['halves'][side] = study_side(doc, side, prefix, mounts, report, label)
            candidate['summary'] = summarize(candidate)
            report['candidates'][label] = candidate
            log(label, candidate['summary'])
        report['study_execution_complete'] = True
    finally:
        # Explicitly discard every in-memory recipe change; never save this doc.
        A.closeDocument(doc.Name)
        report['native_source_unchanged'] = sha(SOURCE) == report['source_sha256']
        report['inputs_unchanged'] = all(sha(ROOT / p) == digest for p, digest in report['inputs'].items())
        if not report['native_source_unchanged'] or not report['inputs_unchanged']:
            report['study_execution_complete'] = False
            report['error'] = 'Source or enumerated input changed during the run; results cannot be accepted.'
        (OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    if not report.get('study_execution_complete'):
        raise RuntimeError('Study incomplete; inspect report.json.')
    (OUT / 'README.md').write_text(markdown(report))
    log('Study complete; candidate failures are findings, not a manufacturing release.', OUT / 'report.json')


if __name__ == '__main__':
    code = 0
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc(file=sys.__stderr__)
        code = 1
    sys.__stdout__.flush()
    sys.__stderr__.flush()
    if os.environ.get('FILO_FREECAD_SUBPROCESS') == '1':
        os._exit(code)
    raise SystemExit(code)
