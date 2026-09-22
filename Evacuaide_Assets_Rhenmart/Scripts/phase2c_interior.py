"""
EVACUAIDE - Phase 2c: Interior Furniture / Room Fit-Out (the "loob")
====================================================================
phase2_building.py builds the room ENCLOSURES (walls, stairs, elevators,
workstation desks) from building_layout.json, but most named rooms are empty
boxes. This phase furnishes them to match the blueprint room program so each
space reads as what the evac map labels it:

  F1  Lobby      : reception desk + logo, lobby sofas + coffee table + rug,
                   restroom fixtures (M/F)
  F2-4 Office    : conference table + chairs + wall screen, manager office
                   desk + chair + guest chairs, pantry counter/upper/fridge/
                   table, storage shelving rows, restroom fixtures (M/F)
  F5  Executive  : executive office desk + sofa + rug, board room long table +
                   chairs + screen, exec pantry + storage + restroom fixtures

Furniture is filed into the existing per-floor room collections
(Floor_01_Lobby ... Floor_05_Executive) and every object is named with the
owning F{n}_ prefix so the floor-map renderer and Unity export pick it up.

Idempotent: deletes every furniture object it made (prefix tokens below)
before rebuilding, so run_all can call it every pass.

Units: metres. Footprint 30 x 20, floor_h 3.0, 5 floors.
Run AFTER phase2_building.py in the same Blender session.
"""
import bpy

FLOOR_H = 3.0

# Furniture object-name tokens (used for idempotent cleanup).
FURN_TOKENS = ("_RecDesk", "_LobbyRug", "_LobbyTable", "_Sofa", "_RecChair",
               "_RRM", "_RRF", "_ExecRR", "_ConfTable", "_ConfTLeg",
               "_ConfChair", "_ConfScreen", "_MgrDesk", "_MgrChair",
               "_MgrGuest", "_PantryCounter", "_PantryUpper", "_PantryFridge",
               "_PantryTable", "_StoreShelf", "_ExecRug", "_ExecDesk",
               "_ExecChair", "_ExecSofa", "_BoardTable", "_BoardTLeg",
               "_BoardChair", "_BoardScreen")


def _srgb(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(_srgb(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4))


def mat(name, hexstr, rough=0.7, metal=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    rgb = hexrgb(hexstr)
    if b:
        b.inputs["Base Color"].default_value = (*rgb, 1.0)
        b.inputs["Roughness"].default_value = rough
        b.inputs["Metallic"].default_value = metal
    return m


def get_coll(name):
    """Return the named collection, creating it under the scene root if the
    running scene doesn't already have per-floor room collections (e.g. after
    a fresh phase2_building.py rebuild, which files rooms into Building/Rooms)."""
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


def link_only(ob, c):
    for x in list(ob.users_collection):
        x.objects.unlink(ob)
    c.objects.link(ob)


def clean_previous():
    removed = 0
    for o in list(bpy.data.objects):
        if any(tok in o.name for tok in FURN_TOKENS):
            bpy.data.objects.remove(o, do_unlink=True)
            removed += 1
    return removed


def build_interior():
    removed = clean_previous()

    M_wood = mat("Mat_FWood", "#8A5A34", 0.6)
    M_wood2 = mat("Mat_FWoodDk", "#5E3A20", 0.6)
    M_metal = mat("Mat_FMetal", "#9BA0A6", 0.4, 0.7)
    M_screen = mat("Mat_FScreen", "#101418", 0.2, 0.2)
    M_chair = mat("Mat_FChair", "#26292E", 0.6)
    M_white = mat("Mat_FWhite", "#E8E8E4", 0.5)
    M_porc = mat("Mat_FPorcelain", "#F2F4F5", 0.2)
    M_sofa = mat("Mat_FSofa", "#2E5A78", 0.7)
    M_rug = mat("Mat_FRug", "#B5482E", 0.9)

    def box(name, size, loc, m, coll):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
        ob = bpy.context.active_object
        ob.name = name
        ob.scale = size
        if m:
            ob.data.materials.append(m)
        link_only(ob, coll)
        return ob

    def cyl(name, r, h, loc, m, coll, verts=12):
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, vertices=verts)
        ob = bpy.context.active_object
        ob.name = name
        if m:
            ob.data.materials.append(m)
        link_only(ob, coll)
        return ob

    def restroom(prefix, cx, cy, z, coll, stalls=3):
        for i in range(stalls):
            tx = cx - 1.0 + i * 0.9
            box(f"{prefix}_ToiletStall{i}", (0.4, 0.5, 0.4), (tx, cy + 1.2, z + 0.2), M_porc, coll)
        box(f"{prefix}_Counter", (2.6, 0.5, 0.1), (cx, cy - 1.4, z + 0.85), M_white, coll)
        for i in range(2):
            box(f"{prefix}_Sink{i}", (0.4, 0.35, 0.12), (cx - 0.7 + i * 1.4, cy - 1.4, z + 0.92), M_porc, coll)

    count = 0

    # ---------- FLOOR 1: reception + lobby + restrooms ----------
    c1 = get_coll("Floor_01_Lobby")
    if c1:
        box("F1_RecDesk_Body", (3.0, 0.8, 1.1), (-6.0, 0.5, 0.55), M_wood, c1); count += 1
        box("F1_RecDesk_Top", (3.3, 1.0, 0.08), (-6.0, 0.5, 1.14), M_wood2, c1); count += 1
        box("F1_RecDesk_Logo", (1.4, 0.05, 0.4), (-6.0, -0.35, 0.7), M_metal, c1); count += 1
        box("F1_LobbyRug", (6, 3, 0.03), (0, -6.5, 0.02), M_rug, c1); count += 1
        for i, sx in enumerate((-1.8, 1.8)):
            box(f"F1_Sofa{i}_Seat", (2.0, 0.9, 0.4), (sx, -6.5, 0.30), M_sofa, c1); count += 1
            box(f"F1_Sofa{i}_Back", (2.0, 0.25, 0.5), (sx, -6.95, 0.6), M_sofa, c1); count += 1
        box("F1_LobbyTable", (1.4, 0.8, 0.4), (0, -6.5, 0.22), M_wood, c1); count += 1
        for i, cx in enumerate((-7, -5)):
            cyl(f"F1_RecChair{i}", 0.28, 0.5, (cx, 1.4, 0.25), M_chair, c1, 10); count += 1
        restroom("F1_RRM", 5.5, 7.0, 0, c1); count += 5
        restroom("F1_RRF", 8.6, 7.0, 0, c1); count += 5

    # ---------- FLOORS 2-4: conference, manager, pantry, storage, restrooms ----------
    for f in (2, 3, 4):
        cn = {2: "Floor_02_Office", 3: "Floor_03_Office", 4: "Floor_04_Office"}[f]
        c = get_coll(cn)
        if not c:
            continue
        base = (f - 1) * FLOOR_H
        # conference room (~ x-12, y6)
        box(f"F{f}_ConfTable", (3.6, 1.4, 0.08), (-12, 6, base + 0.74), M_wood, c); count += 1
        for dx in (-1.5, 1.5):
            box(f"F{f}_ConfTLeg{dx:+.0f}", (0.15, 1.0, 0.72), (-12 + dx, 6, base + 0.36), M_wood2, c); count += 1
        for i, (ox, oy) in enumerate([(-1.0, 1.0), (0, 1.0), (1.0, 1.0), (-1.0, -1.0), (0, -1.0), (1.0, -1.0)]):
            cyl(f"F{f}_ConfChair{i}", 0.28, 0.5, (-12 + ox, 6 + oy, base + 0.25), M_chair, c, 10); count += 1
        # wall-mounted screen flat on the conference room's west wall (thin in
        # X, wide in Y) - kept inside the inner wall face so it never pokes out
        box(f"F{f}_ConfScreen", (0.08, 2.0, 1.1), (-14.75, 6, base + 1.5), M_screen, c); count += 1
        # manager office (~ x0, y7)
        box(f"F{f}_MgrDesk", (1.8, 0.9, 0.08), (0, 7, base + 0.74), M_wood2, c); count += 1
        box(f"F{f}_MgrDeskBody", (1.7, 0.8, 0.7), (0, 7, base + 0.37), M_wood, c); count += 1
        box(f"F{f}_MgrChairS", (0.5, 0.5, 0.08), (0, 7.8, base + 0.46), M_chair, c); count += 1
        box(f"F{f}_MgrChairB", (0.5, 0.08, 0.55), (0, 8.05, base + 0.72), M_chair, c); count += 1
        for gx in (-0.6, 0.6):
            cyl(f"F{f}_MgrGuest{gx:+.0f}", 0.26, 0.5, (gx, 6.2, base + 0.25), M_chair, c, 10); count += 1
        # pantry (~ x7.75, y7)
        box(f"F{f}_PantryCounter", (3.0, 0.6, 0.9), (7.75, 8.5, base + 0.45), M_white, c); count += 1
        box(f"F{f}_PantryUpper", (3.0, 0.4, 0.6), (7.75, 8.7, base + 2.1), M_wood, c); count += 1
        box(f"F{f}_PantryFridge", (0.7, 0.7, 1.6), (6.3, 5.8, base + 0.8), M_metal, c); count += 1
        box(f"F{f}_PantryTable", (1.2, 1.2, 0.06), (8.5, 6.2, base + 0.72), M_wood, c); count += 1
        # storage (~ x7.75, y-6): shelving rows
        for i in range(3):
            box(f"F{f}_StoreShelf{i}", (3.0, 0.5, 2.2), (7.75, -8.0 + i * 2.0, base + 1.1), M_metal, c); count += 1
        # restrooms (left side)
        restroom(f"F{f}_RRM", -13.0, -6.0, base, c, stalls=2); count += 5
        restroom(f"F{f}_RRF", -10.4, -6.0, base, c, stalls=2); count += 5

    # ---------- FLOOR 5: executive, board room, pantry, storage, exec restroom ----------
    c5 = get_coll("Floor_05_Executive")
    if c5:
        base = 4 * FLOOR_H
        box("F5_ExecRug", (4, 3, 0.03), (10, 4, base + 0.02), M_rug, c5); count += 1
        box("F5_ExecDesk", (2.2, 1.0, 0.08), (10, 6, base + 0.76), M_wood2, c5); count += 1
        box("F5_ExecDeskBody", (2.1, 0.9, 0.72), (10, 6, base + 0.38), M_wood, c5); count += 1
        box("F5_ExecChairS", (0.55, 0.55, 0.08), (10, 6.9, base + 0.48), M_chair, c5); count += 1
        box("F5_ExecChairB", (0.55, 0.08, 0.6), (10, 7.2, base + 0.76), M_chair, c5); count += 1
        box("F5_ExecSofa_Seat", (2.4, 0.9, 0.4), (10, 2.2, base + 0.30), M_sofa, c5); count += 1
        box("F5_ExecSofa_Back", (2.4, 0.25, 0.5), (10, 1.75, base + 0.6), M_sofa, c5); count += 1
        box("F5_BoardTable", (5.0, 1.6, 0.08), (-9, 3, base + 0.74), M_wood, c5); count += 1
        for dx in (-2.0, 2.0):
            box(f"F5_BoardTLeg{dx:+.0f}", (0.2, 1.2, 0.72), (-9 + dx, 3, base + 0.36), M_wood2, c5); count += 1
        for i in range(4):
            for oy in (1.15, -1.15):
                cyl(f"F5_BoardChair_{i}_{oy:+.0f}", 0.28, 0.55, (-11 + i * 1.4, 3 + oy, base + 0.27), M_chair, c5, 10); count += 1
        box("F5_BoardScreen", (2.6, 0.08, 1.3), (-9, 5.7, base + 1.6), M_screen, c5); count += 1
        box("F5_PantryCounter", (2.6, 0.6, 0.9), (7.75, 8.5, base + 0.45), M_white, c5); count += 1
        for i in range(2):
            box(f"F5_StoreShelf{i}", (3.0, 0.5, 2.2), (7.75, -7.0 + i * 2.5, base + 1.1), M_metal, c5); count += 1
        restroom("F5_ExecRR", -12.0, -6.0, base, c5, stalls=2); count += 5

    bpy.context.view_layer.update()
    print(f"  removed {removed} old furniture objects")
    return count


if __name__ == "__main__":
    n = build_interior()
    print("=" * 60)
    print(f"PHASE 2c INTERIOR COMPLETE - {n} furniture objects "
          f"(scene total {len(bpy.context.scene.objects)})")
    print("=" * 60)
