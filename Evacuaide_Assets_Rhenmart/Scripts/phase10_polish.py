"""
EVACUAIDE - Phase 10: Design Polish (minimal, high-impact)
==========================================================
Adds the last two things the building was still missing, keeping the poly
budget tiny for Quest VR:

  EXTERIOR
    - Lamp posts around the plaza + parking lot (pole + head + emissive lens),
      giving the campus vertical rhythm and a night-lighting read.

  INTERIOR
    - Continuous skirting / baseboard trim along the four perimeter walls of
      every floor, so wall-to-floor junctions look finished instead of raw.
    - A slim accent reveal band at desk height on the long interior walls.

Everything is authored under names prefixed `POLISH_` and lands in the
`Evacuaide_Polish` collection. The script is IDEMPOTENT: it deletes every
POLISH_ object first, so run_all can call it every pass without duplicating.

Building footprint: X -15..15, Y -10..10. Front = -Y. 5 floors x 3 m.
Units: metres. Blender 5.2.2, pure bpy.
"""
import bpy

FOOT_X, FOOT_Y = 30.0, 20.0
HALF_X, HALF_Y = 15.0, 10.0
FLOOR_H = 3.0
NUM_FLOORS = 5


# ---------------------------------------------------------------- materials
def _srgb(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(_srgb(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4))


def mat_solid(name, hexstr, rough=0.8, metal=0.0):
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


# ---------------------------------------------------------------- helpers
def get_coll(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


def link_only(ob, c):
    for x in list(ob.users_collection):
        x.objects.unlink(ob)
    c.objects.link(ob)


def box(name, size, loc, mat, coll):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    link_only(o, coll)
    return o


def cyl(name, r, h, loc, mat, coll, verts=8):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, vertices=verts, location=loc)
    o = bpy.context.active_object
    o.name = name
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    link_only(o, coll)
    return o


def clear_polish():
    for o in [o for o in bpy.data.objects if o.name.startswith("POLISH_")]:
        bpy.data.objects.remove(o, do_unlink=True)


# ---------------------------------------------------------------- exterior
def build_lamp_posts(coll):
    """Low-poly lamp posts: pole + arm + emissive head lens."""
    m_pole = mat_solid("POLISH_MetalDark", "#2A2E33", rough=0.4, metal=0.85)
    m_lens = mat_emit("POLISH_LampLens", "#FFF3D6", 8.0)
    n = 0

    def lamp(tag, x, y):
        nonlocal n
        base_h = 4.0
        cyl(f"POLISH_LampPole_{tag}", 0.09, base_h, (x, y, base_h / 2), m_pole, coll, verts=8)
        # small cap head
        box(f"POLISH_LampHead_{tag}", (0.5, 0.5, 0.18), (x, y, base_h + 0.02), m_pole, coll)
        # emissive lens underneath the head
        box(f"POLISH_LampLens_{tag}", (0.4, 0.4, 0.06), (x, y, base_h - 0.08), m_lens, coll)
        n += 1

    # Flank the plaza (front, -Y) and the walkway to the parking lot.
    plaza_spots = [(-10.5, -11.5), (10.5, -11.5),
                   (-10.5, -19.0), (10.5, -19.0)]
    for i, (x, y) in enumerate(plaza_spots):
        lamp(f"Plaza_{i}", x, y)
    # Parking-lot perimeter lamps.
    lot_spots = [(-18.0, -29.0), (18.0, -29.0),
                 (-18.0, -39.0), (18.0, -39.0), (0.0, -40.0)]
    for i, (x, y) in enumerate(lot_spots):
        lamp(f"Lot_{i}", x, y)
    return n


# ---------------------------------------------------------------- interior
def build_baseboards(coll):
    """Skirting along the 4 perimeter walls + a slim accent reveal band on the
    long side walls, on every floor."""
    m_skirt = mat_solid("POLISH_Skirting", "#3A3D42", rough=0.6)
    m_accent = mat_solid("POLISH_AccentReveal", "#8A9099", rough=0.4, metal=0.3)
    n = 0
    inset = 0.16          # sit just inside the wall inner face
    sk_h = 0.12           # skirting height
    for f in range(NUM_FLOORS):
        z0 = f * FLOOR_H
        zc = z0 + sk_h / 2 + 0.01
        # front / back skirting (runs along X)
        for side, yy in (("F", -HALF_Y + inset), ("B", HALF_Y - inset)):
            box(f"POLISH_Skirt_F{f+1}_{side}", (FOOT_X - 0.6, 0.05, sk_h),
                (0, yy, zc), m_skirt, coll)
            n += 1
        # left / right skirting (runs along Y)
        for side, xx in (("L", -HALF_X + inset), ("R", HALF_X - inset)):
            box(f"POLISH_Skirt_F{f+1}_{side}", (0.05, FOOT_Y - 0.6, sk_h),
                (xx, 0, zc), m_skirt, coll)
            n += 1
        # accent reveal band at ~1.1 m on the two long side walls
        zb = z0 + 1.1
        for side, xx in (("L", -HALF_X + inset), ("R", HALF_X - inset)):
            box(f"POLISH_Reveal_F{f+1}_{side}", (0.03, FOOT_Y - 2.0, 0.05),
                (xx, 0, zb), m_accent, coll)
            n += 1
    return n


# ---------------------------------------------------------------- main
def main():
    clear_polish()
    coll = get_coll("Evacuaide_Polish")
    lamps = build_lamp_posts(coll)
    trims = build_baseboards(coll)
    total = len([o for o in bpy.data.objects if o.name.startswith("POLISH_")])
    print(f"DONE. Polish added: {lamps} lamp posts, {trims} interior trims "
          f"({total} POLISH_ objects total).")


if __name__ == "__main__":
    main()
