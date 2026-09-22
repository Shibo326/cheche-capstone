"""
EVACUAIDE - Phase 2e: Corporate Office Fit-Out (make the "loob" read as offices)
================================================================================
phase2_building.py lays 15 bare workstation desks (F{n}_WS1..WS15 = desk + ped)
per office floor in a 5-col x 3-row bullpen, but with no chairs, monitors,
partitions or clutter they read as empty tables. This phase dresses every
workstation and the open floor so each office floor looks like a working
corporate office - the level of detail a client capstone review expects -
while staying inside the low-poly Meta Quest budget.

Per workstation (WS1..WS15 on F2, F3, F4):
  - ergonomic task chair (seat + back + post + base)
  - monitor on a stand + keyboard + mouse
  - low cubicle partition panels (back + one side) -> corporate cubicle look
  - desk clutter: pen cup + paper tray

Open-floor ambiance (F2-4):
  - carpet-tile field under the bullpen (corporate blue-grey, two-tone)
  - breakout / coffee station counter with stools
  - accent floor plants along the window wall
  - wall clock

IMPORTANT: this phase creates ~680 objects. It builds meshes with bmesh
(bpy.data.objects.new) instead of bpy.ops.mesh.primitive_*_add - the operator
path is ~50x slower here and can stall/crash Blender at this volume.

Naming: F{n}_OFF_*  (idempotent). Reuses phase2c/2d materials where possible.
Run AFTER phase2_building + 2c + 2d in one Blender session.
"""
import bpy
import bmesh

FLOOR_H = 3.0
OFFICE_FLOORS = {2: "Floor_02_Office", 3: "Floor_03_Office", 4: "Floor_04_Office"}
WS_COLS = (-6.5, -4.0, -1.5, 1.0, 3.5)
WS_ROWS = (3.5, 0.0, -3.5)
OFF_TOKENS = ("_OFF_",)


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


# ---- fast primitive builders (bmesh, no operators) ----
def _cube_mesh():
    me = bpy.data.meshes.new("m")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(me)
    bm.free()
    return me


def _cyl_mesh(verts):
    me = bpy.data.meshes.new("m")
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=verts,
                          radius1=1.0, radius2=1.0, depth=1.0)
    bm.to_mesh(me)
    bm.free()
    return me


def _uv_mesh():
    me = bpy.data.meshes.new("m")
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=5, radius=1.0)
    bm.to_mesh(me)
    bm.free()
    return me


def box(name, size, loc, m, coll, rot=None):
    ob = bpy.data.objects.new(name, _cube_mesh())
    ob.scale = size
    ob.location = loc
    if rot:
        ob.rotation_euler = rot
    if m:
        ob.data.materials.append(m)
    coll.objects.link(ob)
    return ob


def cyl(name, r, h, loc, m, coll, verts=10, rot=None):
    ob = bpy.data.objects.new(name, _cyl_mesh(verts))
    ob.scale = (r, r, h)
    ob.location = loc
    if rot:
        ob.rotation_euler = rot
    if m:
        ob.data.materials.append(m)
    coll.objects.link(ob)
    return ob


def sphere(name, r, loc, m, coll):
    ob = bpy.data.objects.new(name, _uv_mesh())
    ob.scale = (r, r, r)
    ob.location = loc
    if m:
        ob.data.materials.append(m)
    coll.objects.link(ob)
    return ob


def clean_previous():
    removed = 0
    for o in list(bpy.data.objects):
        if any(t in o.name for t in OFF_TOKENS):
            bpy.data.objects.remove(o, do_unlink=True)
            removed += 1
    return removed


def build_office():
    removed = clean_previous()

    Mc = mat("Mat_FChair", "#26292E", 0.6)
    Mm = mat("Mat_FMetal", "#9BA0A6", 0.4, 0.7)
    Ms = mat("Mat_OFF_Screen", "#0A2A3A", 0.15, emit="#12303F", emit_str=0.6)
    Mk = mat("Mat_OFF_Key", "#1A1D21", 0.5)
    Mp = mat("Mat_OFF_Partition", "#6E7B86", 0.8)
    Mpt = mat("Mat_OFF_PartTrim", "#3A4149", 0.5, 0.4)
    Mca = mat("Mat_OFF_Carpet", "#3E4A57", 0.95)
    Mca2 = mat("Mat_OFF_Carpet2", "#48545F", 0.95)
    Mw = mat("Mat_FWood", "#8A5A34", 0.6)
    Mwh = mat("Mat_FWhite", "#E8E8E4", 0.5)
    Ml = mat("Mat_Leaf2", "#3C7E33", 0.9)
    Mpo = mat("Mat_Planter", "#7A6A55", 0.85)
    Mcu = mat("Mat_OFF_Cup", "#C24A3A", 0.5)
    Mtr = mat("Mat_OFF_Tray", "#2A2E33", 0.6)

    def workstation(pfx, x, y, z, c, face):
        dz = z + 0.8
        cy = y + face * 0.55
        cyl(f"{pfx}_ChairSeat", 0.26, 0.10, (x, cy, z + 0.48), Mc, c, 10)
        box(f"{pfx}_ChairBack", (0.46, 0.08, 0.5), (x, cy + face * 0.24, z + 0.78), Mc, c)
        cyl(f"{pfx}_ChairPost", 0.04, 0.4, (x, cy, z + 0.26), Mm, c, 8)
        cyl(f"{pfx}_ChairBase", 0.28, 0.05, (x, cy, z + 0.06), Mm, c, 10)
        my = y - face * 0.30
        # slightly larger monitor for correct desk proportion
        box(f"{pfx}_Monitor", (0.72, 0.05, 0.44), (x, my, dz + 0.33), Ms, c)
        box(f"{pfx}_MonStand", (0.08, 0.08, 0.22), (x, my, dz + 0.10), Mm, c)
        box(f"{pfx}_MonFoot", (0.30, 0.18, 0.03), (x, my, dz + 0.015), Mm, c)
        box(f"{pfx}_Keyboard", (0.44, 0.16, 0.02), (x, y + face * 0.05, dz + 0.02), Mk, c)
        box(f"{pfx}_Mouse", (0.06, 0.09, 0.02), (x + 0.33, y + face * 0.05, dz + 0.02), Mk, c)
        cyl(f"{pfx}_PenCup", 0.05, 0.11, (x - 0.52, my + face * 0.05, dz + 0.06), Mcu, c, 8)
        box(f"{pfx}_Tray", (0.3, 0.22, 0.05), (x + 0.46, my, dz + 0.03), Mtr, c)
        # single low back partition only (cleaner, less cramped than 3-sided);
        # sits just behind the monitor, height keeps sightlines open
        box(f"{pfx}_PartBack", (1.4, 0.04, 0.42), (x, y - face * 0.46, dz + 0.21), Mp, c)
        box(f"{pfx}_PartBackTrim", (1.4, 0.05, 0.04), (x, y - face * 0.46, dz + 0.44), Mpt, c)

    n = 0
    for f, cn in OFFICE_FLOORS.items():
        c = get_coll(cn)
        base = (f - 1) * FLOOR_H
        box(f"F{f}_OFF_Carpet", (13.5, 11.0, 0.02), (-1.5, 0.0, base + 0.02), Mca, c); n += 1
        box(f"F{f}_OFF_CarpetInlay", (11.5, 3.0, 0.03), (-1.5, 0.0, base + 0.025), Mca2, c); n += 1
        idx = 0
        for ry, y in enumerate(WS_ROWS):
            face = -1 if ry < 2 else 1
            for x in WS_COLS:
                idx += 1
                workstation(f"F{f}_OFF_WS{idx}", x, y, base, c, face)
                n += 13
        box(f"F{f}_OFF_Breakout", (2.6, 0.6, 0.9), (11.5, -6.0, base + 0.45), Mwh, c); n += 1
        box(f"F{f}_OFF_BreakUpper", (2.6, 0.4, 0.5), (11.5, -6.2, base + 2.0), Mw, c); n += 1
        cyl(f"F{f}_OFF_CoffeeMk", 0.18, 0.35, (10.7, -6.0, base + 1.08), Mm, c, 8); n += 1
        for i, sx in enumerate((10.4, 11.5, 12.6)):
            cyl(f"F{f}_OFF_Stool_{i}", 0.2, 0.5, (sx, -5.0, base + 0.25), Mc, c, 10); n += 1
        for i, px in enumerate((-11, -8, 8, 11)):
            cyl(f"F{f}_OFF_PlantPot_{i}", 0.3, 0.55, (px, -9.0, base + 0.27), Mpo, c, 10); n += 1
            sphere(f"F{f}_OFF_PlantLeaf_{i}", 0.6, (px, -9.0, base + 1.05), Ml, c); n += 1
        cyl(f"F{f}_OFF_Clock", 0.35, 0.05, (6.0, 9.8, base + 2.2), Mwh, c, 14,
            rot=(1.5708, 0, 0)); n += 1

    bpy.context.view_layer.update()
    print(f"  removed {removed} old office objects")
    return n


if __name__ == "__main__":
    n = build_office()
    print("=" * 60)
    print(f"PHASE 2e OFFICE FIT-OUT COMPLETE - {n} objects "
          f"(scene total {len(bpy.context.scene.objects)})")
    print("=" * 60)
