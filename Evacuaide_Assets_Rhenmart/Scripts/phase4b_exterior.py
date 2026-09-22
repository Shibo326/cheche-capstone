"""
EVACUAIDE - Phase 4b: Exterior Environment / Corporate Campus Site
==================================================================
Builds the surrounding site so the tower reads as a real corporate campus
instead of a box on a small lawn. Everything lands in collection
`Evacuaide_Exterior` (+ sub-collections) so it exports cleanly and the floor
maps / interior are untouched.

Adds:
  - Large two-tone landscaped lawn (site 100 x 100)
  - Raised entrance plaza (front, -Y) with a concrete border + central walkway
  - Glass + steel main-entrance canopy over the front door, with planters
  - Striped parking lot (front, 2 rows x 9 stalls) with a drive-aisle line
  - Rear ASSEMBLY / MUSTER POINT: concrete pad + emissive green ring marker
    (the evacuation gathering point) + a path from the rear emergency exit
  - Perimeter + entrance landscaping (trees, shrubs)

Building footprint: X -15..15, Y -10..10. Front = -Y, Rear = +Y.
Units: metres. Blender 5.2.2, pure bpy.

Idempotent: deletes every EXT_ object (keeps/relocates EVAC_AssemblyMarker)
before rebuilding, so run_all can call it every pass.
"""
import bpy


def _srgb(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(_srgb(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4))


def mat_solid(name, hexstr, rough=0.85, metal=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    rgb = hexrgb(hexstr)
    if b:
        b.inputs["Base Color"].default_value = (*rgb, 1.0)
        b.inputs["Roughness"].default_value = rough
        b.inputs["Metallic"].default_value = metal
    return m


def mat_emit(name, hexstr, strength):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    rgb = hexrgb(hexstr)
    if b:
        b.inputs["Base Color"].default_value = (*rgb, 1.0)
        if "Emission Color" in b.inputs:
            b.inputs["Emission Color"].default_value = (*rgb, 1.0)
        if "Emission Strength" in b.inputs:
            b.inputs["Emission Strength"].default_value = strength
    return m


def get_coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def link_only(ob, c):
    for x in list(ob.users_collection):
        x.objects.unlink(ob)
    c.objects.link(ob)


def box(name, size, loc, mat, coll):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = size
    if mat:
        ob.data.materials.append(mat)
    link_only(ob, coll)
    return ob


def cyl(name, r, h, loc, mat, coll, verts=16):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, vertices=verts)
    ob = bpy.context.active_object
    ob.name = name
    if mat:
        ob.data.materials.append(mat)
    link_only(ob, coll)
    return ob


def clean_previous():
    for o in list(bpy.data.objects):
        if o.name.startswith("EXT_"):
            bpy.data.objects.remove(o, do_unlink=True)


def build_exterior():
    clean_previous()

    m_grass = mat_solid("Mat_Grass", "#4C8C3A", 0.95)
    m_grass2 = mat_solid("Mat_GrassDark", "#3B6E2E", 0.95)
    m_conc = mat_solid("Mat_ConcSite", "#C4C4BC", 0.88)
    m_asph = mat_solid("Mat_Asphalt", "#33343A", 0.9)
    m_paint = mat_emit("Mat_LinePaint", "#F2F2E8", 0.25)
    m_canopy = mat_solid("Mat_Canopy", "#5C6166", 0.5, 0.4)
    m_cglass = mat_solid("Mat_CanopyGlass", "#2A6E7A", 0.08, 0.9)
    m_trunk = mat_solid("Mat_Trunk", "#5A3A1A", 0.9)
    m_leaf = mat_solid("Mat_Leaf", "#2F6B28", 0.9)
    m_leaf2 = mat_solid("Mat_Leaf2", "#3C7E33", 0.9)
    m_assem = mat_emit("Mat_ExitSign", "#00FF88", 3.0)
    m_curb = mat_solid("Mat_Curb", "#9A9A92", 0.8)
    m_planter = mat_solid("Mat_Planter", "#7A6A55", 0.85)

    root = get_coll("Evacuaide_Exterior")
    lot = get_coll("Exterior_Parking", root)
    asm = get_coll("Exterior_Assembly", root)
    trees = get_coll("Exterior_Trees", root)
    n = 0

    # ---- large landscaped ground (site 100 x 100), two-tone ----
    box("EXT_Lawn", (100, 100, 0.1), (0, 0, -0.28), m_grass, root); n += 1
    box("EXT_LawnStripe", (100, 20, 0.02), (0, -30, -0.22), m_grass2, root); n += 1

    # ---- entrance plaza (front -Y), raised concrete + border ----
    box("EXT_Plaza", (24, 10, 0.14), (0, -15.5, -0.18), m_conc, root); n += 1
    box("EXT_PlazaBorder", (25, 11, 0.05), (0, -15.5, -0.24), m_curb, root); n += 1
    box("EXT_Walk", (5, 26, 0.14), (0, -28, -0.17), m_conc, root); n += 1

    # ---- entrance canopy (glass + steel) over front door ----
    box("EXT_CanopyRoof", (9, 4.5, 0.2), (0, -12.0, 3.1), m_canopy, root); n += 1
    box("EXT_CanopyGlass", (8.2, 3.8, 0.06), (0, -12.0, 3.22), m_cglass, root); n += 1
    for sx in (-4.0, 4.0):
        cyl(f"EXT_CanopyPost_{'L' if sx < 0 else 'R'}", 0.14, 3.1,
            (sx, -13.4, 1.55), m_canopy, root, 12); n += 1

    # ---- parking lot (front, further out) 2 rows x 9 stalls ----
    lot_cy = -34
    box("EXT_Lot", (40, 13, 0.14), (0, lot_cy, -0.18), m_asph, lot); n += 1
    stall_w = 2.6
    for r, cy in enumerate((lot_cy + 3.2, lot_cy - 3.2)):
        for i in range(9):
            x = -4 * stall_w + i * stall_w
            box(f"EXT_Stall_{r}_{i}", (0.1, 4.8, 0.02), (x, cy, -0.10), m_paint, lot); n += 1
    box("EXT_AisleLine", (38, 0.12, 0.02), (0, lot_cy, -0.10), m_paint, lot); n += 1

    # ---- rear ASSEMBLY / MUSTER POINT (key for evac training) ----
    box("EXT_AssemblyPad", (20, 14, 0.14), (0, 20, -0.18), m_conc, asm); n += 1
    box("EXT_AssemblyBorder", (21, 15, 0.05), (0, 20, -0.24), m_curb, asm); n += 1
    mk = bpy.data.objects.get("EVAC_AssemblyMarker")
    if mk:
        mk.location = (0, 20, 0.02)
    else:
        cyl("EVAC_AssemblyMarker", 3.2, 0.06, (0, 20, 0.02), m_assem, asm, 48); n += 1
    cyl("EXT_MusterRing", 3.2, 0.04, (0, 20, 0.05), m_assem, asm, 48); n += 1
    cyl("EXT_MusterRingInner", 2.4, 0.05, (0, 20, 0.055), m_conc, asm, 48); n += 1
    box("EXT_RearWalk", (4, 10, 0.14), (0, 13, -0.17), m_conc, asm); n += 1

    # ---- landscaping: perimeter trees + entrance planters ----
    def tree(name, x, y, scale, mleaf):
        cyl(f"{name}_Trunk", 0.22 * scale, 2.4 * scale, (x, y, 1.2 * scale), m_trunk, trees, 8)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1.5 * scale, location=(x, y, 3.1 * scale),
                                             segments=12, ring_count=8)
        ob = bpy.context.active_object
        ob.name = f"{name}_Canopy"
        ob.data.materials.append(mleaf)
        link_only(ob, trees)

    tpos = [(-40, -40, 1.1), (40, -40, 1.1), (-40, 38, 1.0), (40, 38, 1.0),
            (-44, -8, 1.2), (44, -8, 1.2), (-44, 10, 1.1), (44, 10, 1.1),
            (-16, -26, 0.9), (16, -26, 0.9)]
    for i, (x, y, s) in enumerate(tpos):
        tree(f"EXT_Tree_{i}", x, y, s, m_leaf if i % 2 else m_leaf2); n += 2

    for sx in (-6.5, 6.5):
        tag = 'L' if sx < 0 else 'R'
        box(f"EXT_Planter_{tag}", (1.4, 4.0, 0.6), (sx, -15.5, 0.05), m_planter, root); n += 1
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(sx, -15.5, 0.8),
                                             segments=10, ring_count=6)
        ob = bpy.context.active_object
        ob.name = f"EXT_Shrub_{tag}"
        ob.data.materials.append(m_leaf2)
        link_only(ob, trees); n += 1

    bpy.context.view_layer.update()
    return n


if __name__ == "__main__":
    n = build_exterior()
    print("=" * 60)
    print(f"PHASE 4b EXTERIOR COMPLETE - {n} exterior objects "
          f"(scene total {len(bpy.context.scene.objects)})")
    print("=" * 60)
