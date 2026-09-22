"""
EVACUAIDE - Phase 2b: Curtain-Wall Facade (makes the tower READ, not a box)
===========================================================================
phase2_building.py rebuilds the blueprint tower from building_layout.json, but
the perimeter is a set of SOLID full-height walls (F{f}_Wall_{F/B/L/R}) plus
opaque interior windows. That reads as a plain gray concrete box and hides any
glazing placed outside it.

This phase turns that shell into a real corporate curtain-wall system WITHOUT
touching the interior room layout or the export groupings:

  1. Retints the shared materials to a clean corporate palette (warm precast
     frame + reflective blue-green glazing).
  2. Reshapes each perimeter wall into a SPANDREL (low sill band) + HEADER
     (top band), leaving the middle of every floor face open.
  3. Removes the old opaque interior perimeter windows (F*_Win_F / F*_Win_B).
  4. Fills every floor face on all four sides with reflective curtain-wall
     glass, a vertical mullion grid, and a per-floor COLOR ACCENT band that
     matches the evac-map floor coding (F1 grey / F2 blue / F3 green /
     F4 gold / F5 maroon) - this is the signature element tying the 3D tower
     to the 2D floor maps.
  5. Adds corner + mid-span pilasters, a rooftop parapet, HVAC units, a
     roof-access penthouse and a front sign band, plus a double-height glazed
     main entrance.

Idempotent: re-running deletes the FAC_ collection and any _Hdr headers it
made, then rebuilds, so run_all can call it every pass.

Footprint 30 x 20, floor_h 3.0, 5 floors. Front = -Y. Units: metres.
Run AFTER phase2_building.py in the same Blender session.
"""

import bpy

FOOT_X, FOOT_Y = 30.0, 20.0
HALF_X, HALF_Y = 15.0, 10.0
FLOOR_H = 3.0
NFLOORS = 5
TOTAL_H = FLOOR_H * NFLOORS

# Per-floor accent color = evac-map floor coding.
FLOOR_HEX = {1: "#9AA0A6", 2: "#4A90D9", 3: "#5A8A5A", 4: "#C8A830", 5: "#8B2020"}

BAND_BOT = 0.9   # spandrel / sill band height (bottom of each floor face)
BAND_TOP = 0.5   # header band height (top of each floor face)
FAC_COLL = "Evacuaide_Facade"


# ---------------------------------------------------------------- helpers
def _srgb(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(_srgb(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4))


def _bsdf(m):
    return m.node_tree.nodes.get("Principled BSDF") if (m and m.use_nodes) else None


def retint(name, base=None, rough=None, metal=None, alpha=None,
           emit=None, emit_str=None, create=False):
    m = bpy.data.materials.get(name)
    if m is None:
        if not create:
            return None
        m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = _bsdf(m)
    if not b:
        return m
    if base is not None:
        a = alpha if alpha is not None else b.inputs["Alpha"].default_value
        b.inputs["Base Color"].default_value = (*base, a)
    if rough is not None:
        b.inputs["Roughness"].default_value = rough
    if metal is not None:
        b.inputs["Metallic"].default_value = metal
    if alpha is not None:
        b.inputs["Alpha"].default_value = alpha
        m.blend_method = 'BLEND' if alpha < 1.0 else 'OPAQUE'
    if emit is not None and "Emission Color" in b.inputs:
        b.inputs["Emission Color"].default_value = (*emit, 1.0)
    if emit_str is not None and "Emission Strength" in b.inputs:
        b.inputs["Emission Strength"].default_value = emit_str
    return m


def mat_solid(name, hexstr, rough=0.6, metal=0.0):
    return retint(name, base=hexrgb(hexstr), rough=rough, metal=metal, create=True)


def get_collection(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def link_only(ob, coll):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll.objects.link(ob)


def box(name, size, loc, mat, coll):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = size
    if mat:
        ob.data.materials.append(mat)
    link_only(ob, coll)
    return ob


# ---------------------------------------------------------------- clean previous run
def clean_previous():
    # delete FAC_ collection contents
    fc = bpy.data.collections.get(FAC_COLL)
    if fc:
        for o in list(fc.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    # delete any header duplicates from a prior run
    for o in list(bpy.data.objects):
        if o.name.endswith("_Hdr") and "_Wall_" in o.name:
            bpy.data.objects.remove(o, do_unlink=True)


# ---------------------------------------------------------------- material palette
def retint_palette():
    # warm precast frame
    retint("Mat_Wall", base=hexrgb("#CCCCC7"), rough=0.75, metal=0.0)
    mat_solid("Mat_Precast", "#CCCCC7", 0.75, 0.0)
    mat_solid("Mat_Pilaster", "#BFC1BE", 0.65, 0.0)
    # Curtain-wall glazing: tinted blue-teal, semi-reflective but clearly
    # reads as glass from every angle (avoids a full mirror that dissolves
    # into a bright sky and looks like an open face).
    m = mat_solid("Mat_Facade_Glass", "#2C5A66", 0.12)
    b = _bsdf(m)
    if b:
        b.inputs["Metallic"].default_value = 0.55
        b.inputs["Alpha"].default_value = 0.9
        if "Emission Color" in b.inputs:
            b.inputs["Emission Color"].default_value = (*hexrgb("#12333B"), 1.0)
        if "Emission Strength" in b.inputs:
            b.inputs["Emission Strength"].default_value = 0.25
    m.blend_method = 'BLEND'
    mat_solid("Mat_Mullion", "#2D3236", 0.4, 0.7)
    mat_solid("Mat_Roof", "#54585C", 0.8)
    mat_solid("Mat_HVAC", "#8A8E92", 0.5, 0.5)
    mat_solid("Mat_SignBand", "#16202B", 0.4, 0.2)
    # clear-ish interior perimeter glass (if any survive elsewhere)
    retint("Mat_Glass", base=hexrgb("#8CB8D2"), rough=0.05, metal=0.0, alpha=0.30)


# ---------------------------------------------------------------- perimeter -> frame
def reshape_perimeter():
    """Turn each solid perimeter wall into a spandrel + header, leaving the
    glazing zone of every floor face open."""
    reshaped = 0
    for f in range(1, NFLOORS + 1):
        base = (f - 1) * FLOOR_H
        for side in ("F", "B", "L", "R"):
            o = bpy.data.objects.get(f"F{f}_Wall_{side}")
            if not o:
                continue
            dz = o.dimensions.z
            if dz <= 0:
                continue
            # SPANDREL: shrink existing wall to bottom band
            o.scale.z = o.scale.z * (BAND_BOT / dz)
            o.location.z = base + BAND_BOT / 2.0
            # HEADER: duplicate to top band
            hdr = o.copy()
            hdr.data = o.data.copy()
            hdr.name = o.name + "_Hdr"
            link_only(hdr, o.users_collection[0])
            hdr.scale.z = o.scale.z * (BAND_TOP / BAND_BOT)
            hdr.location.z = base + FLOOR_H - BAND_TOP / 2.0
            reshaped += 1
    return reshaped


def remove_opaque_windows():
    removed = 0
    for o in list(bpy.data.objects):
        if "_Win_F" in o.name or "_Win_B" in o.name:
            bpy.data.objects.remove(o, do_unlink=True)
            removed += 1
    return removed


# ---------------------------------------------------------------- curtain wall
def build_curtain_wall(coll):
    n = 0
    m_glass = bpy.data.materials["Mat_Facade_Glass"]
    m_mull = bpy.data.materials["Mat_Mullion"]
    m_pil = bpy.data.materials["Mat_Pilaster"]

    inset = 0.02
    glass_h = FLOOR_H - 0.4  # nearly full floor height

    # pilasters: corners + mid-spans, full height
    pil_w = 0.6
    xs = [-HALF_X, -HALF_X / 2, 0.0, HALF_X / 2, HALF_X]
    for xi, x in enumerate(xs):
        for yi, y in enumerate((-HALF_Y, HALF_Y)):
            box(f"FAC_Pil_X{xi}_Y{yi}", (pil_w, pil_w, TOTAL_H),
                (x, y + (0.12 if y < 0 else -0.12), TOTAL_H / 2), m_pil, coll)
            n += 1
    for yi, y in enumerate((-HALF_Y / 2, 0, HALF_Y / 2)):
        for x in (-HALF_X, HALF_X):
            box(f"FAC_PilSide_{'L' if x < 0 else 'R'}_{yi}",
                (pil_w, pil_w, TOTAL_H),
                (x + (0.12 if x < 0 else -0.12), y, TOTAL_H / 2), m_pil, coll)
            n += 1

    # per-floor glazing + accent band on all four sides
    for f in range(1, NFLOORS + 1):
        base = (f - 1) * FLOOR_H
        accent = mat_solid(f"Mat_Accent{f}", FLOOR_HEX[f], 0.5, 0.1)
        z_glass = base + FLOOR_H / 2.0
        z_band = base + FLOOR_H - BAND_TOP / 2.0
        # front (-Y) / rear (+Y)
        for side, yy in (("F", -HALF_Y), ("B", HALF_Y)):
            yface = yy - (inset if yy < 0 else -inset)
            box(f"FAC_Glass_{side}{f}", (FOOT_X - 1.6, 0.05, glass_h),
                (0, yface, z_glass), m_glass, coll)
            n += 1
            box(f"FAC_Band_{side}{f}", (FOOT_X - 1.2, 0.14, BAND_TOP + 0.05),
                (0, yface, z_band), accent, coll)
            n += 1
            cols = int((FOOT_X - 1.6) // 2.5)
            span = (FOOT_X - 1.6)
            for i in range(cols + 1):
                mx = -span / 2 + i * (span / cols)
                box(f"FAC_Mul_{side}{f}_{i}", (0.08, 0.09, glass_h),
                    (mx, yface, z_glass), m_mull, coll)
                n += 1
        # left (-X) / right (+X)
        for side, xx in (("L", -HALF_X), ("R", HALF_X)):
            xface = xx - (inset if xx < 0 else -inset)
            box(f"FAC_Glass_{side}{f}", (0.05, FOOT_Y - 1.6, glass_h),
                (xface, 0, z_glass), m_glass, coll)
            n += 1
            box(f"FAC_Band_{side}{f}", (0.14, FOOT_Y - 1.2, BAND_TOP + 0.05),
                (xface, 0, z_band), accent, coll)
            n += 1
            rows = int((FOOT_Y - 1.6) // 2.5)
            span = (FOOT_Y - 1.6)
            for i in range(rows + 1):
                my = -span / 2 + i * (span / rows)
                box(f"FAC_Mul_{side}{f}_{i}", (0.09, 0.08, glass_h),
                    (xface, my, z_glass), m_mull, coll)
                n += 1
    return n


def build_entrance(coll):
    n = 0
    m_glass = bpy.data.materials["Mat_Facade_Glass"]
    m_mull = bpy.data.materials["Mat_Mullion"]
    ent_w, ent_h = 8.0, 5.4
    yface = -HALF_Y - 0.12
    box("FAC_Entrance_Glass", (ent_w, 0.06, ent_h), (0, yface, ent_h / 2), m_glass, coll); n += 1
    box("FAC_Entrance_FrameT", (ent_w + 0.3, 0.14, 0.3), (0, yface, ent_h), m_mull, coll); n += 1
    for sx in (-ent_w / 2, 0, ent_w / 2):
        box(f"FAC_Entrance_MulV_{sx:.0f}", (0.12, 0.14, ent_h),
            (sx, yface, ent_h / 2), m_mull, coll); n += 1
    return n


def build_roof(coll):
    n = 0
    m_precast = bpy.data.materials["Mat_Precast"]
    m_roof = bpy.data.materials["Mat_Roof"]
    m_hvac = bpy.data.materials["Mat_HVAC"]
    m_mull = bpy.data.materials["Mat_Mullion"]
    m_sign = bpy.data.materials["Mat_SignBand"]
    rz = TOTAL_H
    par_h, pt = 0.9, 0.25
    box("FAC_Parapet_F", (FOOT_X, pt, par_h), (0, -HALF_Y, rz + par_h / 2), m_precast, coll); n += 1
    box("FAC_Parapet_B", (FOOT_X, pt, par_h), (0, HALF_Y, rz + par_h / 2), m_precast, coll); n += 1
    box("FAC_Parapet_L", (pt, FOOT_Y, par_h), (-HALF_X, 0, rz + par_h / 2), m_precast, coll); n += 1
    box("FAC_Parapet_R", (pt, FOOT_Y, par_h), (HALF_X, 0, rz + par_h / 2), m_precast, coll); n += 1
    box("FAC_RoofDeck", (FOOT_X - 0.6, FOOT_Y - 0.6, 0.1), (0, 0, rz + 0.05), m_roof, coll); n += 1
    for i, (hx, hy) in enumerate([(-6, 3), (0, -3), (6, 4)]):
        box(f"FAC_HVAC_{i}", (2.2, 1.6, 1.1), (hx, hy, rz + 0.65), m_hvac, coll); n += 1
    box("FAC_Penthouse", (3.2, 3.2, 2.6), (11, 7, rz + 1.3), m_precast, coll); n += 1
    box("FAC_Penthouse_Door", (0.9, 0.06, 2.1), (11, 7 - 1.6, rz + 1.05), m_mull, coll); n += 1
    box("FAC_SignBand", (10, 0.2, 1.0), (0, -HALF_Y - 0.2, rz + 0.6), m_sign, coll); n += 1
    return n


# ---------------------------------------------------------------- main
def build_facade():
    clean_previous()
    retint_palette()
    coll = get_collection(FAC_COLL)
    reshaped = reshape_perimeter()
    removed = remove_opaque_windows()
    n = build_curtain_wall(coll)
    n += build_entrance(coll)
    n += build_roof(coll)
    bpy.context.view_layer.update()
    print(f"  perimeter walls reshaped: {reshaped}, opaque windows removed: {removed}")
    return n


if __name__ == "__main__":
    n = build_facade()
    print("=" * 60)
    print(f"PHASE 2b FACADE COMPLETE - {n} facade objects "
          f"(scene total {len(bpy.context.scene.objects)})")
    print("=" * 60)
