"""
EVACUAIDE - PHASE 1: Complete 5-Floor Building Generator
========================================================
VR-Based Earthquake Preparedness & Training Simulation (Unity / Meta Quest).

Generates the full structural building per the APPROVED FLOOR LAYOUT blueprint:
  - 5 floors, 3 m each, 15 m total height
  - 30 m x 20 m floor plate footprint
  - Walls (0.3 m thick), doors (2.1 m high), windows (1.2 m high, 0.9 m sill)
  - Stairwell A (far left) + Stairwell B (far right), 3 m wide x 6 m deep
  - Elevator bank: 2 shafts, 2 m x 2 m each, side by side
  - All rooms per floor, placed to match the approved evacuation-map blueprint
  - Per-floor color-coded floor slabs

UNITS: Blender units = METERS (1 unit = 1 m). Matches spec numbers directly.
       FBX export later uses Scale 0.01 (Phase 6) for Unity.

COORDINATE SYSTEM:
  Origin = building center at ground level.
  X: -15 (left)  ..  +15 (right)      -> 30 m wide
  Y: -10 (front) ..  +10 (rear/back)  -> 20 m deep
  Z: up. Floor F base at (F-1) * FLOOR_H.

Run inside Blender: Scripting workspace -> Run Script.
Pure bpy, no external dependencies. Blender 5.2.2 LTS.
"""

import bpy
import math

# ----------------------------------------------------------------------
# CONFIG (all values in METERS, per spec)
# ----------------------------------------------------------------------
FOOTPRINT_X = 30.0          # building width  (X)
FOOTPRINT_Y = 20.0          # building depth  (Y)
FLOOR_H     = 3.0           # per-floor height
NUM_FLOORS  = 5
WALL_T      = 0.3           # wall thickness
SLAB_T      = 0.2           # floor slab thickness

DOOR_H      = 2.1
DOOR_W_SGL  = 0.9
DOOR_W_DBL  = 1.8
WIN_H       = 1.2
WIN_SILL    = 0.9

STAIR_W     = 3.0           # stairwell width  (X extent)
STAIR_D     = 6.0           # stairwell depth  (Y extent)
ELEV_SIZE   = 2.0           # each elevator shaft 2 x 2

HALF_X = FOOTPRINT_X / 2.0  # 15
HALF_Y = FOOTPRINT_Y / 2.0  # 10

# Per-floor color coding (linear-ish RGB approximations of the hex spec)
FLOOR_COLORS = {
    1: (0.216, 0.216, 0.216),   # concrete gray  #808080
    2: (0.075, 0.278, 0.700),   # steel blue     #4A90D9
    3: (0.106, 0.267, 0.106),   # sage green     #5A8A5A
    4: (0.588, 0.400, 0.030),   # warm yellow    #C8A830
    5: (0.290, 0.016, 0.016),   # executive red  #8B2020
}

# ----------------------------------------------------------------------
# MATERIAL HELPERS
# ----------------------------------------------------------------------
_MAT_CACHE = {}

def _srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def hex_rgb(hexstr):
    hexstr = hexstr.lstrip("#")
    r = int(hexstr[0:2], 16) / 255.0
    g = int(hexstr[2:4], 16) / 255.0
    b = int(hexstr[4:6], 16) / 255.0
    return (_srgb_to_linear(r), _srgb_to_linear(g), _srgb_to_linear(b))

def mat_solid(name, rgb, rough=0.7, metal=0.0):
    key = ("solid", name)
    if key in _MAT_CACHE:
        return _MAT_CACHE[key]
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
    _MAT_CACHE[key] = m
    return m

def mat_glass(name, rgb=(0.55, 0.72, 0.85)):
    key = ("glass", name)
    if key in _MAT_CACHE:
        return _MAT_CACHE[key]
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.05
        bsdf.inputs["Metallic"].default_value = 0.0
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = 0.35
        if "Transmission Weight" in bsdf.inputs:
            bsdf.inputs["Transmission Weight"].default_value = 0.85
    m.blend_method = 'BLEND' if hasattr(m, "blend_method") else m.blend_method
    _MAT_CACHE[key] = m
    return m

def mat_emissive(name, hexstr, strength):
    key = ("emit", name)
    if key in _MAT_CACHE:
        return _MAT_CACHE[key]
    rgb = hex_rgb(hexstr)
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (*rgb, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = strength
    _MAT_CACHE[key] = m
    return m

# ----------------------------------------------------------------------
# GEOMETRY HELPERS
# ----------------------------------------------------------------------
def box(name, size, loc, mat=None, collection=None):
    """Create a cuboid. size=(sx,sy,sz) full dimensions, loc=(x,y,z) center."""
    sx, sy, sz = size
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (sx, sy, sz)
    if mat:
        ob.data.materials.append(mat)
    if collection is not None:
        _link_to(ob, collection)
    return ob

def _link_to(ob, coll):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll.objects.link(ob)

def get_collection(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c

def wall_segment(name, p0, p1, height, base_z, mat, thickness=WALL_T, coll=None):
    """Axis-aligned wall from p0=(x,y) to p1=(x,y)."""
    x0, y0 = p0
    x1, y1 = p1
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    length = math.hypot(x1 - x0, y1 - y0)
    if abs(x1 - x0) >= abs(y1 - y0):
        size = (length, thickness, height)
    else:
        size = (thickness, length, height)
    return box(name, size, (cx, cy, base_z + height / 2.0), mat, coll)

# ----------------------------------------------------------------------
# SCENE RESET
# ----------------------------------------------------------------------
def clean_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras,
                  bpy.data.lights):
        for b in list(block):
            if b.users == 0:
                block.remove(b)
    # remove leftover collections (keep master scene collection)
    for c in list(bpy.data.collections):
        try:
            bpy.data.collections.remove(c)
        except Exception:
            pass
    _MAT_CACHE.clear()

print("=" * 60)
print("EVACUAIDE PHASE 1 - Building generation starting")
print("=" * 60)

# ----------------------------------------------------------------------
# SHARED MATERIALS
# ----------------------------------------------------------------------
def build_materials():
    m = {}
    m["wall"]      = mat_solid("Mat_Wall",     hex_rgb("#D8D8D0"), rough=0.85)
    m["wall_int"]  = mat_solid("Mat_WallInt",  hex_rgb("#C4C0B8"), rough=0.9)
    m["concrete"]  = mat_solid("Mat_Concrete", hex_rgb("#9A9A9A"), rough=0.95)
    m["stair"]     = mat_solid("Mat_Stair",    hex_rgb("#6E7378"), rough=0.8)
    m["elev"]      = mat_solid("Mat_Elevator", hex_rgb("#3A3E44"), rough=0.4, metal=0.6)
    m["glass"]     = mat_glass("Mat_Glass")
    m["door"]      = mat_solid("Mat_Door",     hex_rgb("#7A5230"), rough=0.6)
    m["exit_door"] = mat_emissive("Mat_ExitGreen", "#00FF88", 3.0)
    for f, col in FLOOR_COLORS.items():
        m[f"floor{f}"] = mat_solid(f"Mat_Floor{f}", col, rough=0.85)
    return m

# ----------------------------------------------------------------------
# STRUCTURAL SHELL  (slabs, perimeter walls, windows) per floor
# ----------------------------------------------------------------------
def build_floor_shell(f, mats, coll):
    """Floor slab + perimeter walls with window strips + ceiling for floor f."""
    base = (f - 1) * FLOOR_H
    fmat = mats[f"floor{f}"]

    # ---- floor slab (color coded) ----
    box(f"F{f}_Slab", (FOOTPRINT_X, FOOTPRINT_Y, SLAB_T),
        (0, 0, base - SLAB_T / 2.0), fmat, coll)

    # ---- ceiling slab (top of this floor) ----
    box(f"F{f}_Ceiling", (FOOTPRINT_X, FOOTPRINT_Y, SLAB_T),
        (0, 0, base + FLOOR_H + SLAB_T / 2.0), mats["concrete"], coll)

    wall_h = FLOOR_H
    wmat = mats["wall"]

    # Perimeter walls (4 sides). We use solid walls; window strips are a
    # thin emissive-free glass band added on top for VR readability.
    # left  (x = -HALF_X)
    wall_segment(f"F{f}_Wall_L", (-HALF_X, -HALF_Y), (-HALF_X, HALF_Y),
                 wall_h, base, wmat, coll=coll)
    # right (x = +HALF_X)
    wall_segment(f"F{f}_Wall_R", (HALF_X, -HALF_Y), (HALF_X, HALF_Y),
                 wall_h, base, wmat, coll=coll)
    # front (y = -HALF_Y)
    wall_segment(f"F{f}_Wall_F", (-HALF_X, -HALF_Y), (HALF_X, -HALF_Y),
                 wall_h, base, wmat, coll=coll)
    # rear  (y = +HALF_Y)
    wall_segment(f"F{f}_Wall_B", (-HALF_X, HALF_Y), (HALF_X, HALF_Y),
                 wall_h, base, wmat, coll=coll)

    # ---- window strips on front & rear facades (visual) ----
    win_z = base + WIN_SILL + WIN_H / 2.0
    for side, yy in (("F", -HALF_Y), ("B", HALF_Y)):
        box(f"F{f}_Win_{side}", (FOOTPRINT_X * 0.7, 0.08, WIN_H),
            (0, yy, win_z), mats["glass"], coll)

    return base

# ----------------------------------------------------------------------
# STAIRWELLS  (A far-left, B far-right) - same position every floor
# ----------------------------------------------------------------------
def build_stairwell(tag, f, mats, coll, x_center):
    """Enclosed stairwell shaft + flight. x_center is the shaft centre X."""
    base = (f - 1) * FLOOR_H
    # place stairwell against front area, spanning STAIR_D in Y
    y_center = -HALF_Y + STAIR_D / 2.0 + 0.3
    x0 = x_center - STAIR_W / 2.0
    x1 = x_center + STAIR_W / 2.0
    y0 = y_center - STAIR_D / 2.0
    y1 = y_center + STAIR_D / 2.0
    h = FLOOR_H

    smat = mats["stair"]
    # three enclosing walls (open side faces interior)
    wall_segment(f"F{f}_Stair{tag}_Wo", (x0, y0), (x0, y1), h, base, smat, coll=coll)
    wall_segment(f"F{f}_Stair{tag}_Wf", (x0, y0), (x1, y0), h, base, smat, coll=coll)
    wall_segment(f"F{f}_Stair{tag}_Wb", (x0, y1), (x1, y1), h, base, smat, coll=coll)

    # stair flight (simple stepped ramp of boxes)
    steps = 10
    run = STAIR_D / steps
    rise = FLOOR_H / steps
    for s in range(steps):
        box(f"F{f}_Stair{tag}_Step{s}",
            (STAIR_W - 0.4, run, rise),
            (x_center, y0 + run * (s + 0.5), base + rise * (s + 0.5)),
            smat, coll)
    return (x_center, y_center)

# ----------------------------------------------------------------------
# ELEVATOR BANK  (2 shafts side by side, DO NOT USE)
# ----------------------------------------------------------------------
def build_elevators(f, mats, coll, center_xy):
    base = (f - 1) * FLOOR_H
    cx, cy = center_xy
    h = FLOOR_H
    gap = 0.15
    xs = [cx - (ELEV_SIZE / 2.0 + gap / 2.0), cx + (ELEV_SIZE / 2.0 + gap / 2.0)]
    made = []
    for i, x in enumerate(xs, 1):
        # shaft box (hollow-look: just an enclosure + door face)
        box(f"F{f}_Elev{i}_Shaft", (ELEV_SIZE, ELEV_SIZE, h),
            (x, cy, base + h / 2.0), mats["elev"], coll)
        # door face (front) - the red X / DO NOT USE sign gets added in Phase 4
        box(f"F{f}_Elev{i}_Door", (ELEV_SIZE * 0.8, 0.06, DOOR_H),
            (x, cy - ELEV_SIZE / 2.0 - 0.03, base + DOOR_H / 2.0),
            mats["elev"], coll)
        made.append((x, cy))
    return made

# ----------------------------------------------------------------------
# ROOM builder: 4 low interior partition walls with a door gap on one side
# ----------------------------------------------------------------------
def build_room(name, f, mats, coll, x0, y0, x1, y1, door="S", door_w=DOOR_W_SGL):
    """Interior room from (x0,y0) to (x1,y1). 'door' side: N/S/E/W gap."""
    base = (f - 1) * FLOOR_H
    h = FLOOR_H
    wmat = mats["wall_int"]
    xa, xb = min(x0, x1), max(x0, x1)
    ya, yb = min(y0, y1), max(y0, y1)
    cx = (xa + xb) / 2.0

    def seg(tag, a, b):
        wall_segment(f"F{f}_{name}_{tag}", a, b, h, base, wmat, coll=coll)

    # South wall (y=ya) - optional door gap
    if door == "S":
        gx = cx
        seg("S1", (xa, ya), (gx - door_w / 2.0, ya))
        seg("S2", (gx + door_w / 2.0, ya), (xb, ya))
    else:
        seg("S", (xa, ya), (xb, ya))
    # North wall (y=yb)
    if door == "N":
        gx = cx
        seg("N1", (xa, yb), (gx - door_w / 2.0, yb))
        seg("N2", (gx + door_w / 2.0, yb), (xb, yb))
    else:
        seg("N", (xa, yb), (xb, yb))
    # West wall (x=xa)
    cy = (ya + yb) / 2.0
    if door == "W":
        seg("W1", (xa, ya), (xa, cy - door_w / 2.0))
        seg("W2", (xa, cy + door_w / 2.0), (xa, yb))
    else:
        seg("W", (xa, ya), (xa, yb))
    # East wall (x=xb)
    if door == "E":
        seg("E1", (xb, ya), (xb, cy - door_w / 2.0))
        seg("E2", (xb, cy + door_w / 2.0), (xb, yb))
    else:
        seg("E", (xb, ya), (xb, yb))

# ----------------------------------------------------------------------
# EXIT DOOR (emissive green marker in a facade)
# ----------------------------------------------------------------------
def exit_door(name, f, mats, coll, x, y, w=DOOR_W_DBL):
    base = (f - 1) * FLOOR_H
    box(f"F{f}_{name}", (w, 0.12, DOOR_H),
        (x, y, base + DOOR_H / 2.0), mats["exit_door"], coll)

# ======================================================================
# FIXED ANCHORS (consistent every floor per blueprint)
# ======================================================================
STAIR_A_X = -12.0   # far left
STAIR_B_X =  12.0   # far right

# ======================================================================
# FLOOR 1 - LOBBY
# ======================================================================
def build_floor1(mats, coll):
    f = 1
    build_floor_shell(f, mats, coll)
    build_stairwell("A", f, mats, coll, STAIR_A_X)
    build_stairwell("B", f, mats, coll, STAIR_B_X)

    # LEFT SIDE: Security Office x2 (upper-left, lower-left of stairwell A)
    build_room("SecurityUpper", f, mats, coll, -15, 3, -9, 9, door="E")
    build_room("SecurityLower", f, mats, coll, -15, -9, -9, -3, door="E")
    # Reception Desk x2 (center-left area)
    build_room("Reception1", f, mats, coll, -8, 2, -3.5, 7, door="S")
    build_room("Reception2", f, mats, coll, -8, -6, -3.5, -1, door="N")

    # CENTER: Elevator Bank x2 (center-top, side by side) DO NOT USE
    build_elevators(f, mats, coll, (0.0, 6.5))
    # Main Lobby is the large open center area (no interior walls) -> implicit

    # RIGHT SIDE: Restrooms M/F (upper right), Janitor Closet x2 (upper right)
    build_room("RestroomM", f, mats, coll, 4, 5, 7, 9, door="W")
    build_room("RestroomF", f, mats, coll, 7.2, 5, 10, 9, door="W")
    build_room("Janitor1", f, mats, coll, 4, 1, 7, 4.5, door="W")
    build_room("Janitor2", f, mats, coll, 7.2, 1, 10, 4.5, door="W")

    # EXITS
    exit_door("MainExit", f, mats, coll, 0.0, -HALF_Y, w=DOOR_W_DBL)
    exit_door("EmergencyExitRear", f, mats, coll, 0.0, HALF_Y, w=DOOR_W_DBL)
    return coll

# ======================================================================
# FLOORS 2-4 - OPEN OFFICE (identical)
# ======================================================================
def build_office_floor(f, mats, coll):
    build_floor_shell(f, mats, coll)
    build_stairwell("A", f, mats, coll, STAIR_A_X)
    build_stairwell("B", f, mats, coll, STAIR_B_X)

    # LEFT SIDE: Conference Room (upper-left), Restrooms M/F (lower-left)
    build_room("Conference", f, mats, coll, -15, 3, -9, 9, door="E")
    build_room("RestroomM", f, mats, coll, -15, -9, -12, -3, door="E")
    build_room("RestroomF", f, mats, coll, -11.9, -9, -9, -3, door="E")

    # CENTER: Manager Office (upper center), Open Office (large center)
    build_room("ManagerOffice", f, mats, coll, -3, 5, 3, 9, door="S")

    # Workstations W1-W12 in 3 rows (partition-less desk blocks)
    _build_workstations(f, mats, coll)

    # RIGHT SIDE: Elevator Bank x2 (right side, DO NOT USE)
    build_elevators(f, mats, coll, (11.0, 0.5))
    # Pantry (upper right), Storage Room (lower right)
    build_room("Pantry", f, mats, coll, 6, 5, 9.5, 9, door="W")
    build_room("Storage", f, mats, coll, 6, -9, 9.5, -3, door="W")

    # EXITS: near Stairwell A (left) and Stairwell B (right)
    exit_door("EmergencyExitLeft", f, mats, coll, STAIR_A_X, HALF_Y, w=DOOR_W_DBL)
    exit_door("EmergencyExitRight", f, mats, coll, STAIR_B_X, HALF_Y, w=DOOR_W_DBL)
    return coll

def _build_workstations(f, mats, coll):
    base = (f - 1) * FLOOR_H
    desk_mat = mats["wall_int"]
    # 3 rows x up to 5 columns across the open center
    rows_y = [3.5, 0.0, -3.5]           # top, middle, bottom
    cols_x = [-6.5, -4.0, -1.5, 1.0, 3.5]
    n = 0
    for r, y in enumerate(rows_y):
        for c, x in enumerate(cols_x):
            n += 1
            # desk top
            box(f"F{f}_WS{n}_Desk", (1.4, 0.8, 0.05),
                (x, y, base + 0.75), desk_mat, coll)
            # 4 legs are overkill for VR; one pedestal
            box(f"F{f}_WS{n}_Ped", (1.2, 0.6, 0.7),
                (x, y, base + 0.35), desk_mat, coll)
    return n

# ======================================================================
# FLOOR 5 - EXECUTIVE
# ======================================================================
def build_floor5(mats, coll):
    f = 5
    build_floor_shell(f, mats, coll)
    build_stairwell("A", f, mats, coll, STAIR_A_X)
    build_stairwell("B", f, mats, coll, STAIR_B_X)

    # LEFT SIDE: Executive Office (large, upper-left), Board Room (lower-left)
    build_room("ExecutiveOffice", f, mats, coll, -15, 2, -6, 9, door="E")
    build_room("BoardRoom", f, mats, coll, -15, -9, -6, -1, door="E")

    # CENTER: Elevator Bank x2 (center, DO NOT USE)
    build_elevators(f, mats, coll, (0.0, 5.5))

    # RIGHT SIDE: Exec Restroom (upper right), Pantry (upper right),
    #             Roof Access (top right), Storage (lower right, small)
    build_room("ExecRestroom", f, mats, coll, 5, 5, 8, 9, door="W")
    build_room("Pantry", f, mats, coll, 8.2, 5, 11, 9, door="W")
    build_room("RoofAccess", f, mats, coll, 11.5, 5, 14.5, 9, door="W")
    build_room("Storage", f, mats, coll, 6, -8, 9, -4, door="W")

    # EXITS: left + right
    exit_door("EmergencyExitLeft", f, mats, coll, STAIR_A_X, HALF_Y, w=DOOR_W_DBL)
    exit_door("EmergencyExitRight", f, mats, coll, STAIR_B_X, HALF_Y, w=DOOR_W_DBL)
    return coll

# ======================================================================
# MAIN
# ======================================================================
def main():
    clean_scene()
    mats = build_materials()

    root = get_collection("Evacuaide_Building")
    per_floor = {}

    # Floor 1
    c1 = get_collection("Floor_01_Lobby", root)
    build_floor1(mats, c1); per_floor[1] = c1
    # Floors 2-4
    for f in (2, 3, 4):
        cf = get_collection(f"Floor_0{f}_Office", root)
        build_office_floor(f, mats, cf); per_floor[f] = cf
    # Floor 5
    c5 = get_collection("Floor_05_Executive", root)
    build_floor5(mats, c5); per_floor[5] = c5

    bpy.context.view_layer.update()
    total = len(bpy.context.scene.objects)
    print("=" * 60)
    print(f"PHASE 1 COMPLETE - {total} objects created")
    print("=" * 60)
    return total

if __name__ == "__main__":
    main()
