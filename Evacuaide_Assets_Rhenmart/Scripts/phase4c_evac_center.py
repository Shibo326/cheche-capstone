"""
EVACUAIDE - Phase 4c: Standalone Evacuation / Relief Center (SEPARATE building)
===============================================================================
Client requirement: the evacuation center must be a SEPARATE building, OUTSIDE
and away from the office tower. During an earthquake it is unsafe to shelter
inside the same high-rise being evacuated, so the muster point + relief center
sit on open ground at the rear of the site, well clear of the tower footprint.

This phase builds that separate single-storey structure and connects it to the
existing rear muster ring (created in phase4b at world (0, 20)) with a marked
evacuation path. It never touches the office tower or its interior.

Layout (world space, metres; tower is X -15..15, Y -10..10, rear = +Y):
  - Tower rear wall ............... y = +10
  - Rear muster ring (phase4b) .... y = +20
  - THIS evacuation center ........ centred at y = +38  (≈ 28 m behind tower)

The center is a LOW, open-span, seismically-safe hall (single storey, 3.2 m,
wide clear span, big doors, low parapet) - deliberately not a tower:
  - Concrete slab pad + low perimeter walls with two wide entrances (front)
  - Light flat roof on columns (open, quick-exit design)
  - Big green cross + backlit "EVACUATION CENTER" / "EVACUATION CENTER" sign
  - Interior relief fit-out: rows of cots, first-aid station, water dispenser +
    supply crates, folding tables + benches, directory board
  - Green emissive guidance: a walkway + directional arrows from the tower
    muster ring straight to the center entrance, and an "ASSEMBLY -> CENTER"
    marker

Naming: everything is prefixed `EC_` (evac center) and filed in a dedicated
`Evacuaide_EvacCenter` collection so it exports cleanly and the tower / floor
maps are unaffected.

Idempotent: deletes every EC_ object first, so run_all can call it each pass.
Run AFTER phase4b_exterior.py (needs the muster ring) in the same session.
"""
import bpy

# ---- site placement --------------------------------------------------------
CTR_Y = 38.0           # evac center centre (well behind tower rear wall y=+10)
HALL_W = 24.0          # hall width  (X span)
HALL_D = 16.0          # hall depth  (Y span)
WALL_H = 3.2           # low single storey
WALL_T = 0.3
MUSTER_Y = 20.0        # phase4b muster ring centre


def _srgb(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(_srgb(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4))


def mat(name, hexstr, rough=0.8, metal=0.0):
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
    m = mat(name, hexstr, 0.5)
    b = m.node_tree.nodes.get("Principled BSDF")
    if b:
        if "Emission Color" in b.inputs:
            b.inputs["Emission Color"].default_value = (*hexrgb(hexstr), 1.0)
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


def box(name, size, loc, m, coll):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = size
    if m:
        ob.data.materials.append(m)
    link_only(ob, coll)
    return ob


def cyl(name, r, h, loc, m, coll, verts=16):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, vertices=verts)
    ob = bpy.context.active_object
    ob.name = name
    if m:
        ob.data.materials.append(m)
    link_only(ob, coll)
    return ob


def clean_previous():
    removed = 0
    for o in list(bpy.data.objects):
        if o.name.startswith("EC_"):
            bpy.data.objects.remove(o, do_unlink=True)
            removed += 1
    return removed


def build_evac_center():
    removed = clean_previous()

    m_slab = mat("Mat_EC_Slab", "#B9BAB4", 0.9)
    m_wall = mat("Mat_EC_Wall", "#E4E5E1", 0.85)
    m_col = mat("Mat_EC_Col", "#C7C9C4", 0.7)
    m_roof = mat("Mat_EC_Roof", "#4E6E5A", 0.7)          # green relief-tent roof
    m_green = mat_emit("Mat_EC_Green", "#00C070", 2.0)   # safety green
    m_sign = mat("Mat_EC_SignBoard", "#0E3A2A", 0.5)
    m_signT = mat_emit("Mat_EC_SignText", "#EAFBF2", 1.6)
    m_cross = mat_emit("Mat_EC_Cross", "#25E08A", 2.5)
    m_cot = mat("Mat_EC_Cot", "#33538A", 0.7)            # blue cots
    m_cotleg = mat("Mat_EC_CotLeg", "#8A8E92", 0.4, 0.6)
    m_table = mat("Mat_EC_Table", "#9A7A4A", 0.6)
    m_bench = mat("Mat_EC_Bench", "#6E5A3A", 0.6)
    m_crate = mat("Mat_EC_Crate", "#B5732E", 0.7)
    m_water = mat("Mat_EC_Water", "#7FB6D6", 0.15)
    m_aid = mat_emit("Mat_EC_Aid", "#00D24A", 1.5)
    m_arrow = mat_emit("Mat_EC_Arrow", "#00FF66", 3.0)
    m_path = mat("Mat_EC_Path", "#C4C4BC", 0.88)

    root = get_coll("Evacuaide_EvacCenter")
    n = 0

    hx = HALL_W / 2.0
    hy = HALL_D / 2.0
    y0 = CTR_Y
    z_wall = WALL_H / 2.0
    front_y = y0 - hy   # entrance side (facing the tower / muster point, -Y)
    back_y = y0 + hy

    # ---- ground pad + border ----
    box("EC_Pad", (HALL_W + 4, HALL_D + 4, 0.16), (0, y0, -0.16), m_slab, root); n += 1
    box("EC_PadBorder", (HALL_W + 5, HALL_D + 5, 0.05), (0, y0, -0.22),
        mat("Mat_EC_Curb", "#9A9A92", 0.8), root); n += 1
    # interior finished floor
    box("EC_Floor", (HALL_W - 0.4, HALL_D - 0.4, 0.04), (0, y0, 0.03),
        mat("Mat_EC_FloorFin", "#3C4A44", 0.7), root); n += 1

    # ---- perimeter low walls (open, quick-exit): back + sides solid,
    #      front has two wide entrances (gap in the middle) ----
    box("EC_Wall_Back", (HALL_W, WALL_T, WALL_H), (0, back_y, z_wall), m_wall, root); n += 1
    box("EC_Wall_L", (WALL_T, HALL_D, WALL_H), (-hx, y0, z_wall), m_wall, root); n += 1
    box("EC_Wall_R", (WALL_T, HALL_D, WALL_H), (hx, y0, z_wall), m_wall, root); n += 1
    # front wall split into three piers leaving two 4 m entrances
    pier_w = (HALL_W - 2 * 4.0) / 3.0
    xs = [-hx + pier_w / 2,
          0.0,
          hx - pier_w / 2]
    for i, px in enumerate(xs):
        w = pier_w if i != 1 else pier_w
        box(f"EC_Wall_FrontPier_{i}", (w, WALL_T, WALL_H), (px, front_y, z_wall), m_wall, root); n += 1
    # header beam across the whole front (above the door openings)
    box("EC_Wall_FrontHeader", (HALL_W, WALL_T, 0.5), (0, front_y, WALL_H - 0.25), m_wall, root); n += 1

    # ---- columns + flat roof (open hall) ----
    for cx in (-hx + 1.0, 0.0, hx - 1.0):
        for cy in (front_y + 1.0, y0, back_y - 1.0):
            cyl(f"EC_Col_{cx:.0f}_{cy:.0f}", 0.2, WALL_H, (cx, cy, z_wall), m_col, root, 10); n += 1
    box("EC_Roof", (HALL_W + 1.2, HALL_D + 1.2, 0.25), (0, y0, WALL_H + 0.12), m_roof, root); n += 1
    box("EC_RoofParapet_F", (HALL_W + 1.2, 0.2, 0.4), (0, front_y - 0.6, WALL_H + 0.4), m_wall, root); n += 1

    # ---- big green cross + backlit sign over the entrance ----
    box("EC_Sign_Board", (8.0, 0.2, 1.4), (0, front_y - 0.75, WALL_H + 0.5), m_sign, root); n += 1
    box("EC_Sign_TextEN", (6.0, 0.06, 0.5), (0, front_y - 0.86, WALL_H + 0.75), m_signT, root); n += 1
    box("EC_Sign_TextFIL", (6.0, 0.06, 0.35), (0, front_y - 0.86, WALL_H + 0.30), m_green, root); n += 1
    # green safety cross on the front, above the sign
    box("EC_Cross_V", (0.5, 0.12, 1.6), (0, front_y - 0.9, WALL_H + 2.1), m_cross, root); n += 1
    box("EC_Cross_H", (1.4, 0.12, 0.5), (0, front_y - 0.9, WALL_H + 2.1), m_cross, root); n += 1

    # ---- interior relief fit-out ----
    # rows of cots (blue) with legs
    cot_rows = [y0 - 4.5, y0 - 1.5, y0 + 1.5, y0 + 4.5]
    cot_xs = [-hx + 3.0, -hx + 6.0, hx - 6.0, hx - 3.0]
    ci = 0
    for ry in cot_rows:
        for cxp in cot_xs:
            box(f"EC_Cot_{ci}", (1.8, 0.7, 0.12), (cxp, ry, 0.42), m_cot, root)
            for lx in (-0.8, 0.8):
                for ly in (-0.3, 0.3):
                    box(f"EC_CotLeg_{ci}_{lx:+.0f}{ly:+.0f}", (0.06, 0.06, 0.36),
                        (cxp + lx, ry + ly, 0.18), m_cotleg, root)
            ci += 1
            n += 5

    # first-aid station (right-back corner): counter + green cross panel
    box("EC_Aid_Counter", (3.0, 0.7, 0.9), (hx - 2.5, back_y - 1.5, 0.45), m_table, root); n += 1
    box("EC_Aid_CrossV", (0.25, 0.05, 0.7), (hx - 2.5, back_y - 0.75, 1.6), m_aid, root); n += 1
    box("EC_Aid_CrossH", (0.7, 0.05, 0.25), (hx - 2.5, back_y - 0.75, 1.6), m_aid, root); n += 1

    # water dispenser + supply crates (left-back corner)
    cyl("EC_Water_Body", 0.24, 1.0, (-hx + 2.0, back_y - 1.6, 0.5), m_wall, root, 12); n += 1
    cyl("EC_Water_Jug", 0.2, 0.4, (-hx + 2.0, back_y - 1.6, 1.2), m_water, root, 12); n += 1
    for i, (crx, cry) in enumerate([(-hx + 3.4, back_y - 1.6), (-hx + 4.3, back_y - 1.6),
                                    (-hx + 3.9, back_y - 1.6)]):
        cz = 0.35 if i < 2 else 1.0
        box(f"EC_Crate_{i}", (0.8, 0.7, 0.7), (crx, cry, cz), m_crate, root); n += 1

    # folding tables + benches (registration / triage, center-front)
    for i, tx in enumerate((-3.0, 3.0)):
        box(f"EC_Table_{i}", (2.4, 1.0, 0.06), (tx, front_y + 2.5, 0.74), m_table, root); n += 1
        box(f"EC_Bench_{i}a", (2.4, 0.35, 0.1), (tx, front_y + 1.9, 0.42), m_bench, root); n += 1
        box(f"EC_Bench_{i}b", (2.4, 0.35, 0.1), (tx, front_y + 3.1, 0.42), m_bench, root); n += 1

    # directory / info board by the entrance
    box("EC_Directory", (1.6, 0.08, 1.1), (hx - 1.2, front_y + 0.4, 1.5), m_sign, root); n += 1

    # ---- guidance from the tower muster ring (y=20) to the center entrance ----
    # concrete connecting walkway
    walk_len = (front_y - MUSTER_Y)
    walk_cy = (MUSTER_Y + front_y) / 2.0
    box("EC_PathWalk", (5.0, walk_len, 0.14), (0, walk_cy, -0.15), m_path, root); n += 1
    # green directional arrows along the path, pointing to the center (+Y)
    steps = 5
    for i in range(steps):
        ay = MUSTER_Y + (i + 0.5) * (walk_len / steps)
        box(f"EC_Arrow_{i}", (0.6, 0.9, 0.04), (0, ay, -0.06), m_arrow, root); n += 1
    # "ASSEMBLY -> CENTER" ground marker just outside the entrance
    box("EC_EntryMarker", (6.0, 1.2, 0.04), (0, front_y - 1.6, -0.05), m_green, root); n += 1

    bpy.context.view_layer.update()
    print(f"  removed {removed} old evac-center objects; center at y={CTR_Y} "
          f"(tower rear wall y=+10, {CTR_Y - 10:.0f} m clear)")
    return n


if __name__ == "__main__":
    n = build_evac_center()
    print("=" * 60)
    print(f"PHASE 4c EVAC CENTER COMPLETE - {n} objects "
          f"(scene total {len(bpy.context.scene.objects)})")
    print("=" * 60)
