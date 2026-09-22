"""
EVACUAIDE - Phase 2f: Corporate Material + Finish Pass (make the loob READ)
==========================================================================
The floors are already FURNISHED (phase2c) and DRESSED with props, ceiling
light panels and a full cubicle fit-out (phase2d_detail + phase2e_office). What
still makes them look unfinished is that almost every surface shares the same
flat mid-gray, and the slab has no floor finish outside the small carpet patch.

This phase adds NO new props. It only:
  1. Retints the SHARED building materials to a clean corporate palette so
     walls, ceilings, stairs, elevators and cores read as finished surfaces
     with real contrast (off-white walls, warm-grey ceiling, etc.).
  2. Lays a full-floor finish layer per level (polished tile in the F1 lobby,
     corporate carpet on F2-4, premium carpet on F5) so there is no bare slab.
  3. Runs a thin accent skirting band + a feature accent stripe around the
     service core, color-coded per floor (subtle, desaturated - professional,
     not the bold facade colors).
  4. Warms the emissive ceiling-panel material and boosts it slightly so the
     interior reads as lit in the VR walkthrough.

Naming: F{n}_FIN_*  (idempotent - deletes its own objects first).
Materials edited in place are shared, so re-running is safe (values are set,
not accumulated).

Footprint 30 x 20, floor_h 3.0, 5 floors. Units: metres.
Run AFTER phase2c / 2d / 2e in the same Blender session (order-independent vs
those, but must be after the shell exists).
"""
import bpy

FOOT_X, FOOT_Y = 30.0, 20.0
HALF_X, HALF_Y = 15.0, 10.0
FLOOR_H = 3.0
NFLOORS = 5

# Muted professional per-floor accent (desaturated vs bold facade bands).
FLOOR_ACCENT = {1: "#5B6570", 2: "#3E6E9E", 3: "#4E7E5A", 4: "#A8842E", 5: "#7E3A3A"}
# Full-floor finish tone per floor.
FLOOR_FINISH = {1: "#3A3D42", 2: "#414852", 3: "#3E463F", 4: "#474038", 5: "#332E30"}


def _srgb(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(_srgb(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4))


def _bsdf(m):
    return m.node_tree.nodes.get("Principled BSDF") if (m and m.use_nodes) else None


def set_mat(name, base=None, rough=None, metal=None, emit=None, emit_str=None):
    """Retint an existing shared material in place (no-op if it doesn't exist)."""
    m = bpy.data.materials.get(name)
    b = _bsdf(m)
    if not b:
        return
    if base is not None:
        b.inputs["Base Color"].default_value = (*hexrgb(base), 1.0)
    if rough is not None:
        b.inputs["Roughness"].default_value = rough
    if metal is not None:
        b.inputs["Metallic"].default_value = metal
    if emit is not None and "Emission Color" in b.inputs:
        b.inputs["Emission Color"].default_value = (*hexrgb(emit), 1.0)
    if emit_str is not None and "Emission Strength" in b.inputs:
        b.inputs["Emission Strength"].default_value = emit_str


def mat(name, hexstr, rough=0.7, metal=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = _bsdf(m)
    if b:
        b.inputs["Base Color"].default_value = (*hexrgb(hexstr), 1.0)
        b.inputs["Roughness"].default_value = rough
        b.inputs["Metallic"].default_value = metal
    return m


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


def box(name, size, loc, m, coll):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = size
    if m:
        ob.data.materials.append(m)
    link_only(ob, coll)
    return ob


def clean_previous():
    removed = 0
    for o in list(bpy.data.objects):
        if "_FIN_" in o.name:
            bpy.data.objects.remove(o, do_unlink=True)
            removed += 1
    return removed


def retint_shared():
    # Interior partitions -> clean office off-white
    set_mat("Mat_WallInt", base="#E6E7E4", rough=0.85, metal=0.0)
    # Perimeter precast already handled by facade; nudge inner face tone
    set_mat("Mat_Wall", base="#D9DAD6", rough=0.75)
    # Ceiling slab -> clean plaster
    set_mat("Mat_Concrete", base="#DBDCD9", rough=0.9)
    # Stairs -> mid corporate grey with a touch of contrast
    set_mat("Mat_Stair", base="#4A4F55", rough=0.7)
    # Elevator core -> brushed dark metal
    set_mat("Mat_Elevator", base="#20242A", rough=0.35, metal=0.7)
    # Cabinet / metal props -> cleaner
    set_mat("Mat_Cabinet", base="#2A2E33", rough=0.4, metal=0.6)
    # Warm + brighten the ceiling light panels (both possible panel materials)
    for pn in ("Mat_DTL_Light", "Mat_CeilPanel"):
        set_mat(pn, base="#FFF6E6", emit="#FFF6E6", emit_str=3.5)


def build():
    removed = clean_previous()
    retint_shared()
    fin = get_coll("Evacuaide_InteriorFinish")

    n = 0
    for f in range(1, NFLOORS + 1):
        base = (f - 1) * FLOOR_H
        finish = mat(f"Mat_FIN_Floor{f}", FLOOR_FINISH[f], 0.6)
        accent = mat(f"Mat_FIN_Accent{f}", FLOOR_ACCENT[f], 0.55)

        # full-floor finish layer just above the slab (leaves stair/elevator
        # cores visible; it's a flat plane so it won't fight furniture).
        # NOTE: skirting/baseboards are owned by phase10_polish - not repeated
        # here to avoid duplicate trim.
        box(f"F{f}_FIN_Floor", (FOOT_X - 0.6, FOOT_Y - 0.6, 0.02),
            (0, 0, base + 0.015), finish, fin)
        n += 1

        # feature accent stripe around the service core (a professional band
        # at mid height on the four core-facing walls near y=+6/-6, x=+-10)
        box(f"F{f}_FIN_AccentBand_B", (FOOT_X - 6.0, 0.03, 0.25),
            (0, HALF_Y - 0.32, base + 1.9), accent, fin)
        n += 1

    bpy.context.view_layer.update()
    print(f"  removed {removed} old finish objects")
    return n


if __name__ == "__main__":
    n = build()
    print("=" * 60)
    print(f"PHASE 2f FINISH COMPLETE - {n} finish objects "
          f"(scene total {len(bpy.context.scene.objects)})")
    print("=" * 60)
