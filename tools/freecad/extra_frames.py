"""Native, additive Flan36 roof variants. No custom proxies or runtime callbacks.

The same recipe is used by the append-only installer and the full generator.
It references the current Smooth solid instead of reconstructing its interfaces.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import hashlib
import json
import math
from pathlib import Path

OWNER = 'flan36-frame-extensions-1'
STYLES = ('cartridge', 'arcade', 'mecha', 'kintsugi')
BOUND_KEYS = ('XMin', 'YMin', 'ZMin', 'XMax', 'YMax', 'ZMax')


def load_spec(root=None):
    root = Path(root) if root else Path(__file__).resolve().parents[2]
    spec = json.loads((root / 'design/frame-extensions.json').read_text())
    if spec['schema'] != OWNER or tuple(spec['styles']) != STYLES:
        raise ValueError('Unexpected extension schema or style set')
    if not 0 < spec['root_overlap_mm'] <= .1 or not 0 < spec['max_relief_mm'] <= .6:
        raise ValueError('Relief exceeds the authorized additive roof scope')
    for style, theme in spec['styles'].items():
        ids = set()
        for item in theme['features']:
            if item['id'] in ids or not item['id'].isalnum():
                raise ValueError((style, 'duplicate/invalid feature name', item['id']))
            ids.add(item['id'])
            if item['role'] not in spec['roles'] or not 0 < item['height_mm'] <= .6:
                raise ValueError((style, item['id'], 'invalid role or height'))
            if item['kind'] not in ('box', 'disc', 'polygon', 'stroke'):
                raise ValueError((style, item['id'], 'unsupported primitive'))
    return spec


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rgb(hexcolor):
    return tuple(int(hexcolor[i:i + 2], 16) / 255 for i in (1, 3, 5))


def fingerprint(shape):
    return hashlib.sha256(shape.exportBrepToString().encode('utf-8')).hexdigest()


def property_value(obj, name, type_id, value):
    if name not in obj.PropertiesList:
        obj.addProperty(type_id, name, 'Flan36')
    setattr(obj, name, value)


def find_smooth(doc, side):
    prefix = 'L_' if side == 'left' else 'R_'
    objects = [o for o in doc.Objects if o.Name.startswith(prefix)
               and o.TypeId != 'App::Link' and getattr(o, 'FrameStyle', '') == 'smooth']
    if len(objects) != 1:
        raise ValueError((side, 'expected exactly one native Smooth frame', len(objects)))
    return objects[0]


def face_role(spec, style, side, face, roof):
    point = face.CenterOfMass
    if point.z <= roof + 1e-4:
        return 'body'
    x = point.x if side == 'left' else spec['mirror_sum_x_mm'] - point.x
    y = -point.y
    for zone in spec['styles'][style]['zones']:
        x0, y0, x1, y1 = zone['xy']
        if x0 <= x <= x1 and y0 <= y <= y1:
            return zone['role']
    return 'detail'


class NativeRecipe:
    """Create or update only objects marked as belonging to this extension.

    Features are native boxes, cylinders, blocked polygon sketches/extrusions,
    a translated native compound, and native Boolean operations. Their parameters
    and expressions remain editable after saving and reopening the document.
    """
    def __init__(self, doc, side, group, spec):
        import FreeCAD as A
        self.A, self.doc, self.side, self.group, self.spec = A, doc, side, group, spec
        self.prefix = ('L_' if side == 'left' else 'R_') + 'ExtraFrame_'
        self.used = []

    def add(self, type_id, suffix):
        name = self.prefix + suffix
        obj = self.doc.getObject(name)
        if obj is None:
            obj = self.doc.addObject(type_id, name)
            property_value(obj, 'FrameExtensionOwner', 'App::PropertyString', OWNER)
        elif obj.TypeId != type_id or getattr(obj, 'FrameExtensionOwner', '') != OWNER:
            raise ValueError(('Refusing to replace an unowned object', name))
        self.group.addObject(obj)
        self.used.append(obj)
        return obj

    def point(self, p, z=0):
        x, y = p
        return self.A.Vector(x if self.side == 'left' else self.spec['mirror_sum_x_mm'] - x, -y, z)

    def roof(self, obj, property_name, height):
        obj.setExpression(property_name, 'Parameters.FrameTop - %.9g mm' % self.spec['root_overlap_mm'])
        property_value(obj, 'ReliefHeight', 'App::PropertyLength', height)

    def polygon(self, name, points, height):
        import Part
        import Sketcher
        sketch = self.add('Sketcher::SketchObject', name + 'Sketch')
        # These are extension-owned sketch segments; never touch original sketches.
        for index in reversed(range(sketch.GeometryCount)):
            sketch.delGeometry(index)
        vectors = [self.point(p) for p in points]
        for a, b in zip(vectors, vectors[1:] + vectors[:1]):
            index = sketch.addGeometry(Part.LineSegment(a, b), False)
            sketch.addConstraint(Sketcher.Constraint('Block', index))
        out = self.add('Part::Extrusion', name)
        out.Base, out.Dir, out.Solid = sketch, self.A.Vector(0, 0, 1), True
        self.roof(out, 'Placement.Base.z', height)
        out.setExpression('LengthFwd', 'ReliefHeight + %.9g mm' % self.spec['root_overlap_mm'])
        return out

    def primitive(self, name, item):
        height = item['height_mm']
        if item['kind'] == 'box':
            x0, y0, x1, y1 = item['xy']
            if x1 <= x0 or y1 <= y0:
                raise ValueError((name, 'invalid rectangle'))
            obj = self.add('Part::Box', name)
            obj.Length, obj.Width = x1 - x0, y1 - y0
            obj.Placement.Base = self.point((x0 if self.side == 'left' else x1, y1))
            self.roof(obj, 'Placement.Base.z', height)
            obj.setExpression('Height', 'ReliefHeight + %.9g mm' % self.spec['root_overlap_mm'])
            return [obj]
        if item['kind'] == 'disc':
            obj = self.add('Part::Cylinder', name)
            obj.Radius = item['radius_mm']
            obj.Placement.Base = self.point(item['xy'])
            self.roof(obj, 'Placement.Base.z', height)
            obj.setExpression('Height', 'ReliefHeight + %.9g mm' % self.spec['root_overlap_mm'])
            return [obj]
        if item['kind'] == 'polygon':
            return [self.polygon(name, item['points'], height)]
        if item['kind'] == 'stroke':
            # Native rectangular extrusions plus round native joints form a stroke.
            out = []
            radius = item['width_mm'] / 2
            for i, (a, b) in enumerate(zip(item['points'], item['points'][1:])):
                dx, dy = b[0] - a[0], b[1] - a[1]
                length = math.hypot(dx, dy)
                if length <= 1e-6:
                    raise ValueError((name, 'zero length stroke'))
                nx, ny = -dy / length * radius, dx / length * radius
                corners = [[a[0]+nx,a[1]+ny],[b[0]+nx,b[1]+ny],
                           [b[0]-nx,b[1]-ny],[a[0]-nx,a[1]-ny]]
                out.append(self.polygon(name + 'Segment' + str(i), corners, height))
            for i, point in enumerate(item['points']):
                out += self.primitive(name + 'Joint' + str(i), dict(kind='disc', xy=point,
                                      radius_mm=radius, height_mm=height))
            return out
        raise ValueError((name, 'unknown primitive'))

    def build(self, smooth, style):
        theme = self.spec['styles'][style]
        pieces = []
        for item in theme['features']:
            nodes = self.primitive(style + '_' + item['id'], item)
            for node in nodes:
                property_value(node, 'ColorRole', 'App::PropertyString', item['role'])
            pieces.extend(nodes)
        raw = self.add('Part::MultiFuse', style + '_RawRelief')
        raw.Shapes, raw.Refine = pieces, True
        mask = self.add('Part::Compound', style + '_RoofMask')
        mask.Links = [smooth]
        # A native moved copy of the actual smooth solid preserves its current
        # contour/window, including manual changes. Below-roof source is never cut.
        mask.Placement.Base = self.A.Vector(0, 0, self.spec['max_relief_mm'])
        clipped = self.add('Part::Common', style + '_SupportedRelief')
        clipped.Base, clipped.Tool, clipped.Refine = raw, mask, True
        for suffix in ('GlassWindow', 'ResetToolAccess', 'USBPlugAccess', 'MCUCornerClearance', 'PowerAccess'):
            tool = self.doc.getObject(('L_' if self.side == 'left' else 'R_') + suffix)
            if tool is None:
                raise ValueError(('Missing current interface tool', suffix))
            cut = self.add('Part::Cut', style + '_' + suffix)
            cut.Base, cut.Tool, cut.Refine = clipped, tool, True
            clipped = cut
        final = self.add('Part::MultiFuse', style + '_Final')
        final.Shapes, final.Refine = [smooth, clipped], True
        final.Label = 'Frame · ' + theme['label'] + ' · variant'
        for name, value in [('FrameStyle', style), ('ModelStatus', 'Nominal study; physical fit untested'),
                            ('ReliefSpecSHA256', hashlib.sha256(json.dumps(theme,sort_keys=True).encode()).hexdigest())]:
            property_value(final, name, 'App::PropertyString', value)
        property_value(final, 'SmoothSource', 'App::PropertyLink', smooth)
        property_value(final, 'PrototypePrintable', 'App::PropertyBool', True)
        property_value(final, 'MaxRelief', 'App::PropertyLength', self.spec['max_relief_mm'])
        return final


def validate_variant(doc, side, smooth, variant, spec):
    import FreeCAD as A
    import Part
    import MeshPart
    roof = doc.Parameters.FrameTop.Value
    base, shape = smooth.Shape, variant.Shape
    if not base.isValid() or len(base.Solids) != 1:
        raise ValueError((smooth.Name, 'invalid source Smooth frame'))
    if not shape.isValid() or len(shape.Solids) != 1:
        raise ValueError((variant.Name, 'invalid/disconnected frame', len(shape.Solids)))
    delta = shape.cut(base)
    removed = base.cut(shape).Volume
    if removed > 1e-5 or delta.Volume < .1:
        raise ValueError((variant.Name, 'source lost or relief absent', removed, delta.Volume))
    if delta.BoundBox.ZMin < roof - 1e-5 or shape.BoundBox.ZMax > roof + spec['max_relief_mm'] + 1e-5:
        raise ValueError((variant.Name, 'relief outside roof band', delta.BoundBox.ZMin, shape.BoundBox.ZMax))
    bounds = {key: abs(getattr(shape.BoundBox, key) - getattr(base.BoundBox, key))
              for key in ('XMin', 'XMax', 'YMin', 'YMax', 'ZMin')}
    if max(bounds.values()) > 1e-5:
        raise ValueError((variant.Name, 'changed XY envelope or underside', bounds))
    # Check actual added geometry has a vertically adjacent source roof below it.
    # A moved copy by max relief is the same support constraint used by the recipe.
    support = base.copy()
    support.translate(A.Vector(0, 0, spec['max_relief_mm']))
    unsupported = delta.cut(support).Volume
    if unsupported > 1e-5:
        raise ValueError((variant.Name, 'unsupported relief', unsupported))
    prefix = 'L_' if side == 'left' else 'R_'
    interfaces = {}
    for suffix in ('GlassWindow', 'ResetToolAccess', 'USBPlugAccess', 'MCUCornerClearance', 'PowerAccess'):
        tool = doc.getObject(prefix + suffix)
        volume = delta.common(tool.Shape).Volume
        interfaces[suffix] = volume
        if volume > 1e-5:
            raise ValueError((variant.Name, 'interface changed', suffix, volume))
    # USB plug and straight-insertion corridor, consistent with export_revI.py.
    x = 116.8 if side == 'left' else 160 - 128.8
    corridor = Part.makeBox(12, 20, 5, A.Vector(x, -18.8, 6.7))
    if shape.common(corridor).Volume > 1e-5:
        raise ValueError((variant.Name, 'USB corridor collision'))
    mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=.03, AngularDeflection=.12, Relative=False)
    if not mesh.isSolid():
        raise ValueError((variant.Name, 'open mesh'))
    return dict(object=variant.Name, source_object=smooth.Name, source_shape_sha256=fingerprint(base),
                shape_sha256=fingerprint(shape), connected_solids=1, closed_mesh=True,
                unchanged_base=True, removed_source_volume_mm3=removed,
                added_roof_volume_mm3=delta.Volume, interface_added_volume_mm3=interfaces,
                bounds_mm=[getattr(shape.BoundBox, k) for k in BOUND_KEYS],
                max_roof_relief_mm=shape.BoundBox.ZMax-roof, manufacturing_ready=False)


def build_for_half(doc, side, smooth=None, history=None, spec=None, validate=True):
    """Shared integration entry point; returns {style_id: native final object}.

    In build_revI.py call after completing the original six styles, before the
    ActiveFrame link is created. Exclude extension IDs from its old generic loop.
    The append-only installer calls exactly this same recipe.
    """
    spec = spec or load_spec()
    prefix = 'L_' if side == 'left' else 'R_'
    smooth = smooth or find_smooth(doc, side)
    history = history or doc.getObject(prefix + 'Construction')
    if history is None:
        raise ValueError('Missing original construction group')
    group_name = prefix + 'ExtraFrames'
    group = doc.getObject(group_name)
    if group is None:
        group = doc.addObject('App::DocumentObjectGroup', group_name)
        property_value(group, 'FrameExtensionOwner', 'App::PropertyString', OWNER)
    elif getattr(group, 'FrameExtensionOwner', '') != OWNER:
        raise ValueError(('Refusing to change unowned group', group_name))
    group.Label = 'Roof variants · Cartridge / Arcade / Mecha / Kintsugi'
    history.addObject(group)
    recipe = NativeRecipe(doc, side, group, spec)
    objects = {style: recipe.build(smooth, style) for style in spec['styles']}
    doc.recompute()
    for style, obj in objects.items():
        if validate:
            validate_variant(doc, side, smooth, obj, spec)
        if obj.ViewObject is not None:
            colors = spec['styles'][style]['colors']
            obj.ViewObject.ShapeColor = rgb(colors['body'])
            obj.ViewObject.LineColor = (.13,.18,.17)
            obj.ViewObject.DiffuseColor = [rgb(colors[face_role(spec, style, side, face,
                                         doc.Parameters.FrameTop.Value)]) for face in obj.Shape.Faces]
    for obj in recipe.used:
        if obj.ViewObject is not None:
            obj.ViewObject.Visibility = False
    if group.ViewObject is not None:
        group.ViewObject.Visibility = False
    return objects
