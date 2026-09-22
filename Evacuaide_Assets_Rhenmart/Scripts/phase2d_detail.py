"""
EVACUAIDE - Phase 2d: Detail Enhancement Pass (capstone polish)
================================================================
Runs AFTER phase2_building / 2b facade / 2c interior / 4b exterior in the same
Blender session. Adds the extra detail the client capstone blueprint calls for
but the earlier phases left out, WITHOUT breaking the low-poly Quest budget
(every prop is boxes/cylinders, 100-400 tris, materials reused).

Grounded in PHASE1_AssetPlan.md:
  Lobby (F1)    : backlit reception logo wall, 4 potted plants, wall directory
                  board, wall clock, entrance mat.
  Office (F2-4) : desktop monitors on the manager desk, water dispenser,
                  printer station, filing cabinets x2, whiteboard, bookshelf.
  Executive(F5) : desk monitor, wall art, bookshelf, mini fridge.
  All floors    : recessed emissive ceiling light panels (readability), a
                  floor-number sign at the stairwell landing.
  Exterior      : parked cars in the lot (low-poly), 2 flagpoles + entrance
                  ground sign, bollard lights along the entry walkway.

Naming: interior -> F{n}_DTL_*, exterior -> EXT_DTL_*  (both idempotent).
Footprint 30 x 20, floor_h 3.0, front = -Y. Units: metres.
"""
import bpy

FLOOR_H = 3.0
NFLOORS = 5
HALF_X, HALF_Y = 15.0, 10.0

DTL_TOKENS = ("_DTL_",)


def _srgb(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(_srgb(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4))


def mat(name, hexstr, rough=0.7, metal=0.0, emit=None, emit_str=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    rgb = hexrgb(hexstr)
    if b:
        b.inputs["Base Color"].default_value = (*rgb, 1.0)
        b.inputs["Roughness"].default_value = rough
        b.inputs["Metallic"].default_value = metal
        if emit is not None and "Emission Color" in b.inputs:
            b.inputs["Emission Color"].default_value = (*hexrgb(emit), 1.0)
        if "Emission Strength" in b.inputs:
            b.inputs["Emission Strength"].default_value = emit_str
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


def box(name, size, loc, m, coll, rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = size
    if rot:
        ob.rotation_euler = rot
    if m:
        ob.data.materials.append(m)
    link_only(ob, coll)
    return ob


def cyl(name, r, h, loc, m, coll, verts=12, rot=None):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, vertices=verts)
    ob = bpy.context.active_object
    ob.name = name
    if rot:
        ob.rotation_euler = rot
    if m:
        ob.data.materials.append(m)
    link_only(ob, coll)
    return ob


def sphere(name, r, loc, m, coll, seg=10, ring=6):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=seg, ring_count=ring)
    ob = bpy.context.active_object
    ob.name = name
    if m:
        ob.data.materials.append(m)
    link_only(ob, coll)
    return ob


def clean_previous():
    removed = 0
    for o in list(bpy.data.objects):
        if any(t in o.name for t in DTL_TOKENS):
            bpy.data.objects.remove(o, do_unlink=True)
            removed += 1
    return removed


def build_detail():
    removed = clean_previous()

    M_wood = bpy.data.materials.get("Mat_FWood") or mat("Mat_FWood", "#8A5A34", 0.6)
    M_metal = bpy.data.materials.get("Mat_FMetal") or mat("Mat_FMetal", "#9BA0A6", 0.4, 0.7)
    M_screen = bpy.data.materials.get("Mat_FScreen") or mat("Mat_FScreen", "#101418", 0.2)
    M_white = bpy.data.materials.get("Mat_FWhite") or mat("Mat_FWhite", "#E8E8E4", 0.5)
    M_leaf = bpy.data.materials.get("Mat_Leaf2") or mat("Mat_Leaf2", "#3C7E33", 0.9)
    M_planter = bpy.data.materials.get("Mat_Planter") or mat("Mat_Planter", "#7A6A55", 0.85)
    M_light = mat("Mat_DTL_Light", "#FFF4E0", 0.3, emit="#FFF4E0", emit_str=2.5)
    M_logo = mat("Mat_DTL_Logo", "#4CC0E0", 0.3, emit="#4CC0E0", emit_str=1.5)
    M_board = mat("Mat_DTL_Board", "#1C2530", 0.4)
    M_glassmon = mat("Mat_DTL_Monitor", "#0A2A3A", 0.15, emit="#153A4E", emit_str=0.8)
    M_mat = mat("Mat_DTL_Mat", "#333A40", 0.9)
    M_carbody = mat("Mat_DTL_Car", "#3A6EA5", 0.35, 0.3)
    M_carglass = mat("Mat_DTL_CarGlass", "#101822", 0.1, 0.4)
    M_tyre = mat("Mat_DTL_Tyre", "#141414", 0.9)
    M_pole = mat("Mat_DTL_Pole", "#B8BBBE", 0.4, 0.6)
    M_flag = mat("Mat_DTL_Flag", "#C8102E", 0.8)
    M_bollard = mat("Mat_DTL_Bollard", "#FFE39A", 0.3, emit="#FFE39A", emit_str=3.0)
    M_signG = mat("Mat_DTL_SignGround", "#123A4A", 0.4)

    n = 0

    # ---- per-floor ceiling light panels + floor-number sign ----
    for f in range(1, NFLOORS + 1):
        cn = {1: "Floor_01_Lobby", 2: "Floor_02_Office", 3: "Floor_03_Office",
              4: "Floor_04_Office", 5: "Floor_05_Executive"}[f]
        c = get_coll(cn)
        base = (f - 1) * FLOOR_H
        zc = base + FLOOR_H - 0.16
        # 3 x 2 grid of recessed light panels
        for ix, gx in enumerate((-8, 0, 8)):
            for iy, gy in enumerate((-4.5, 4.5)):
                box(f"F{f}_DTL_Light_{ix}{iy}", (2.4, 1.2, 0.06), (gx, gy, zc),
                    M_light, c); n += 1
        # floor-number sign near stairwell A (approx -13, 3)
        box(f"F{f}_DTL_FloorSign", (0.9, 0.06, 0.9), (-13.4, 3.0, base + 2.2),
            M_board, c); n += 1

    # ---- F1 lobby extras ----
    c1 = get_coll("Floor_01_Lobby")
    # backlit reception logo wall behind desk
    box("F1_DTL_LogoWall", (3.4, 0.12, 1.6), (-6.0, 1.9, 1.4), M_board, c1); n += 1
    box("F1_DTL_LogoText", (2.4, 0.06, 0.5), (-6.0, 1.78, 1.6), M_logo, c1); n += 1
    # 4 potted plants (blueprint) at lobby corners
    for i, (px, py) in enumerate([(-13.5, -8.5), (13.5, -8.5), (13.5, 8.5), (-13.5, 8.5)]):
        cyl(f"F1_DTL_PotBody_{i}", 0.35, 0.6, (px, py, 0.3), M_planter, c1, 10); n += 1
        sphere(f"F1_DTL_PotLeaf_{i}", 0.7, (px, py, 1.1), M_leaf, c1); n += 1
    # wall directory board + clock + entrance mat
    box("F1_DTL_Directory", (1.6, 0.06, 1.1), (2.5, 9.8, 1.6), M_board, c1); n += 1
    cyl("F1_DTL_Clock", 0.4, 0.06, (-2.0, 9.8, 2.2), M_white, c1, 16,
        rot=(1.5708, 0, 0)); n += 1
    box("F1_DTL_EntranceMat", (5.0, 2.2, 0.02), (0, -9.0, 0.02), M_mat, c1); n += 1

    # ---- F2-4 office extras ----
    for f in (2, 3, 4):
        cn = {2: "Floor_02_Office", 3: "Floor_03_Office", 4: "Floor_04_Office"}[f]
        c = get_coll(cn)
        base = (f - 1) * FLOOR_H
        # dual monitors on the manager desk (0,7)
        for mx in (-0.5, 0.5):
            box(f"F{f}_DTL_Monitor_{mx:+.0f}", (0.7, 0.05, 0.42),
                (mx, 7.15, base + 1.05), M_glassmon, c); n += 1
            box(f"F{f}_DTL_MonStand_{mx:+.0f}", (0.1, 0.1, 0.25),
                (mx, 7.1, base + 0.82), M_metal, c); n += 1
        # water dispenser near pantry
        box(f"F{f}_DTL_WaterDisp", (0.5, 0.5, 1.2), (5.5, 8.6, base + 0.6), M_white, c); n += 1
        cyl(f"F{f}_DTL_WaterBottle", 0.22, 0.5, (5.5, 8.6, base + 1.45),
            M_glassmon, c, 10); n += 1
        # printer station
        box(f"F{f}_DTL_Printer", (0.9, 0.7, 0.5), (12.5, 8.4, base + 0.9), M_metal, c); n += 1
        box(f"F{f}_DTL_PrinterTable", (1.1, 0.9, 0.7), (12.5, 8.4, base + 0.35), M_wood, c); n += 1
        # filing cabinets x2 near cubicles
        for i, cx in enumerate((-6.5, -5.6)):
            box(f"F{f}_DTL_Filing_{i}", (0.6, 0.7, 1.3), (cx, -8.5, base + 0.65),
                M_metal, c); n += 1
        # whiteboard on conference wall
        box(f"F{f}_DTL_Whiteboard", (2.4, 0.05, 1.2), (-9.5, 8.9, base + 1.6),
            M_white, c); n += 1
        # bookshelf
        box(f"F{f}_DTL_Bookshelf", (2.0, 0.4, 2.0), (13.5, 2.0, base + 1.0),
            M_wood, c); n += 1

    # ---- F5 executive extras ----
    c5 = get_coll("Floor_05_Executive")
    base = 4 * FLOOR_H
    for mx in (9.6, 10.4):
        box(f"F5_DTL_Monitor_{mx:.0f}", (0.7, 0.05, 0.42), (mx, 6.15, base + 1.08),
            M_glassmon, c5); n += 1
    box("F5_DTL_WallArt", (1.8, 0.06, 1.1), (13.5, 6.0, base + 1.7), M_logo, c5); n += 1
    box("F5_DTL_ExecBookshelf", (2.2, 0.4, 2.0), (13.6, 2.0, base + 1.0), M_wood, c5); n += 1
    box("F5_DTL_MiniFridge", (0.7, 0.7, 1.0), (6.3, 8.4, base + 0.5), M_metal, c5); n += 1

    # ---- EXTERIOR: parked cars, flagpoles, ground sign, bollards ----
    ext = bpy.data.collections.get("Exterior_Parking") or get_coll("Exterior_Parking")
    root = bpy.data.collections.get("Evacuaide_Exterior") or get_coll("Evacuaide_Exterior")
    lot_cy = -34
    stall_w = 2.6
    car_cols = {0: "#3A6EA5", 1: "#B23A3A", 2: "#4A4F55", 3: "#C9A227",
                4: "#3C7E4A", 5: "#8A8E92"}

    def car(name, x, y, hexstr):
        body_m = mat(f"Mat_DTL_Car_{hexstr[1:]}", hexstr, 0.35, 0.3)
        box(f"{name}_Body", (2.0, 4.2, 0.7), (x, y, 0.35), body_m, ext); 
        box(f"{name}_Cabin", (1.7, 2.4, 0.6), (x, y - 0.2, 0.95), M_carglass, ext)
        for wx, wy in [(-0.85, 1.4), (0.85, 1.4), (-0.85, -1.4), (0.85, -1.4)]:
            cyl(f"{name}_W_{wx:+.0f}{wy:+.0f}", 0.32, 0.25, (x + wx, y + wy, 0.28),
                M_tyre, ext, 10, rot=(0, 1.5708, 0))

    # populate front row of stalls with a few parked cars (not all -> reads real)
    parked = [0, 2, 3, 5, 7]
    for j, i in enumerate(parked):
        x = -4 * stall_w + i * stall_w
        car(f"EXT_DTL_Car_{i}", x, lot_cy + 3.2, list(car_cols.values())[j % 6])
        n += 6

    # two flagpoles + flags flanking the plaza
    for sx in (-9.0, 9.0):
        tag = 'L' if sx < 0 else 'R'
        cyl(f"EXT_DTL_FlagPole_{tag}", 0.08, 7.0, (sx, -20, 3.5), M_pole, root, 8); n += 1
        box(f"EXT_DTL_Flag_{tag}", (1.4, 0.04, 0.9), (sx + 0.75, -20, 6.4), M_flag, root); n += 1

    # entrance ground sign (monument sign) at plaza edge
    box("EXT_DTL_GroundSign_Base", (4.0, 0.8, 1.2), (0, -25.5, 0.6), M_signG, root); n += 1
    box("EXT_DTL_GroundSign_Face", (3.4, 0.1, 0.7), (0, -25.05, 0.85), M_logo, root); n += 1

    # bollard lights along the entry walkway (front)
    for i, wy in enumerate((-24, -28, -32)):
        for sx in (-3.2, 3.2):
            cyl(f"EXT_DTL_Bollard_{i}_{'L' if sx<0 else 'R'}", 0.1, 1.0,
                (sx, wy, 0.5), M_bollard, root, 8); n += 1

    bpy.context.view_layer.update()
    print(f"  removed {removed} old detail objects")
    return n


if __name__ == "__main__":
    n = build_detail()
    print("=" * 60)
    print(f"PHASE 2d DETAIL COMPLETE - {n} detail objects "
          f"(scene total {len(bpy.context.scene.objects)})")
    print("=" * 60)
