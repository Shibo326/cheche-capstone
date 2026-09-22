"""
EVACUAIDE - Phase 7: Automatic Design Polish
============================================
One self-contained pass that takes whatever building .blend is CURRENTLY OPEN
and brings it to a clean, professional training-sim look, then saves a
POLISHED copy and writes a hero render. Safe to re-run (idempotent): it keys
everything off object/material names and rebuilds its own lighting rig each time.

What it does:
  1. Neutralizes big wall/slab surfaces (off-white) so the building reads real,
     not like colored toy blocks -- while KEEPING vivid per-floor accent trim
     for the evacuation color-code (F1 green ... F5 red).
  2. Tunes glass to a tinted, believable curtain-wall look (not milky).
  3. Ensures a clean daylight rig: a single warm key Sun + a Nishita sky,
     AgX view transform for filmic contrast.
  4. Frames a hero camera on the whole building and renders a PNG.
  5. Saves a copy as Evacuaide_Building_POLISHED.blend (does not clobber the
     file you have open).

Run from Blender's Scripting tab (Open -> Run), or headless:
    blender <your_building>.blend --background --python phase7_polish.py

It writes:
    ../Evacuaide_Building_POLISHED.blend
    ../Renders/polished_hero.png
"""

import bpy
import os
import math
import mathutils


# ----------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------
def bsdf_of(mat):
    if not mat or not mat.use_nodes:
        return None
    return mat.node_tree.nodes.get("Principled BSDF")


def tune(name, base=None, rough=None, metal=None, alpha=None):
    """Adjust an existing material by name. No-op if it doesn't exist, so the
    same script works across the slightly different material naming used by
    the various building .blend versions (M_*, Mat_*, Evac_*)."""
    m = bpy.data.materials.get(name)
    if not m:
        return False
    b = bsdf_of(m)
    if not b:
        return False
    if base is not None:
        r, g, bl = base
        b.inputs["Base Color"].default_value = (r, g, bl, 1.0)
        m.diffuse_color = (r, g, bl, alpha if alpha is not None else 1.0)
    if rough is not None:
        b.inputs["Roughness"].default_value = rough
    if metal is not None:
        b.inputs["Metallic"].default_value = metal
    if alpha is not None and "Alpha" in b.inputs:
        b.inputs["Alpha"].default_value = alpha
        if alpha < 1.0:
            try:
                m.blend_method = 'BLEND'
            except Exception:
                pass
    return True


# ----------------------------------------------------------------------
# 1 + 2. Materials: neutral surfaces, vivid accents, believable glass
# ----------------------------------------------------------------------
def polish_materials():
    touched = []

    # --- Big neutral surfaces (walls / slabs / ceilings) -------------
    # Handles every naming variant that appears across the building files.
    neutral_walls = {
        "M_Wall": (0.87, 0.87, 0.85),
        "M_Slab": (0.55, 0.55, 0.57),
        "M_Carpet": (0.26, 0.28, 0.34),
        "M_Column": (0.80, 0.80, 0.78),
        "Evac_Column": (0.82, 0.82, 0.80),
        # legacy Final.blend floor mats -> faint per-floor tint, high value
        "Mat_Floor_01_Lobby": (0.88, 0.90, 0.88),
        "Mat_Floor_02_Office": (0.87, 0.89, 0.92),
        "Mat_Floor_03_Office": (0.92, 0.90, 0.86),
        "Mat_Floor_04_Office": (0.90, 0.88, 0.91),
        "Mat_Floor_05_Executive": (0.91, 0.89, 0.88),
    }
    for name, rgb in neutral_walls.items():
        if tune(name, base=rgb, rough=0.85):
            touched.append(name)

    # --- Vivid per-floor accent trim (both naming schemes) -----------
    accents = {
        1: (0.16, 0.62, 0.26),   # green  - lobby
        2: (0.10, 0.50, 0.88),   # blue
        3: (0.96, 0.56, 0.05),   # orange
        4: (0.55, 0.18, 0.68),   # purple
        5: (0.86, 0.18, 0.16),   # red    - executive
    }
    for i, rgb in accents.items():
        for prefix in ("M_Accent_F", "Evac_Accent_F"):
            if tune(f"{prefix}{i}", base=rgb, rough=0.45):
                touched.append(f"{prefix}{i}")

    # --- Glass: tinted curtain wall, reads solid-ish, not milky ------
    for gname in ("M_Glass", "Evac_Glass", "Mat_Glass"):
        if tune(gname, base=(0.32, 0.46, 0.55), rough=0.06, metal=0.0, alpha=0.32):
            touched.append(gname)

    # --- Mullions / metal frames: dark satin ------------------------
    for mn in ("M_Mullion", "Evac_Mullion", "M_Metal", "Mat_Metal"):
        if tune(mn, rough=0.30, metal=0.85):
            touched.append(mn)

    # --- Roof: dark standing-seam metal -----------------------------
    for rn in ("Evac_Roof",):
        tune(rn, base=(0.16, 0.17, 0.19), rough=0.45, metal=0.7)

    # --- Emergency / evac markers: keep them punchy + emissive -------
    emissive = {
        "MK_ExitGreen": (0.10, 0.80, 0.22),
        "MK_HazardRed": (0.90, 0.12, 0.10),
        "MK_StairBlue": (0.10, 0.40, 0.95),
        "MK_AssemblyYellow": (1.00, 0.80, 0.05),
        "Mat_ExitGreen": (0.10, 0.80, 0.22),
        "Mat_HazardMark": (0.90, 0.12, 0.10),
        "Mat_StairBlue": (0.10, 0.40, 0.95),
        "Mat_AssemblyYel": (1.00, 0.80, 0.05),
    }
    for name, rgb in emissive.items():
        m = bpy.data.materials.get(name)
        if not m:
            continue
        b = bsdf_of(m)
        if not b:
            continue
        b.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1)
        if "Emission Color" in b.inputs:
            b.inputs["Emission Color"].default_value = (rgb[0], rgb[1], rgb[2], 1)
        if "Emission Strength" in b.inputs:
            b.inputs["Emission Strength"].default_value = 2.5
        touched.append(name)

    return touched


# ----------------------------------------------------------------------
# 3. Clean daylight rig + filmic view
# ----------------------------------------------------------------------
def build_lighting():
    scene = bpy.context.scene

    # Remove any prior/placeholder lights so re-runs stay clean.
    for o in [o for o in bpy.data.objects if o.type == 'LIGHT']:
        bpy.data.objects.remove(o, do_unlink=True)

    # Warm key sun with soft shadows.
    sd = bpy.data.lights.new("Sun_Key", type='SUN')
    sd.energy = 4.0
    sd.angle = math.radians(1.8)
    sd.color = (1.0, 0.96, 0.9)
    sun = bpy.data.objects.new("Sun_Key", sd)
    scene.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(52), math.radians(8), math.radians(35))

    # World: Nishita sky if available, else a soft blue gradient.
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_WORLD':
            nt.nodes.remove(n)
    out = nt.nodes.get("World Output") or nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = 1.0
    try:
        sky = nt.nodes.new("ShaderNodeTexSky")
        sky.sky_type = 'NISHITA'
        sky.sun_elevation = math.radians(38)
        sky.sun_rotation = math.radians(35)
        nt.links.new(sky.outputs[0], bg.inputs[0])
    except Exception:
        bg.inputs[0].default_value = (0.55, 0.68, 0.85, 1)
    nt.links.new(bg.outputs[0], out.inputs[0])

    # Filmic tone mapping for contrast/depth.
    try:
        scene.view_settings.view_transform = 'AgX'
    except Exception:
        pass

    # Engine: prefer EEVEE Next, fall back to EEVEE.
    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except Exception:
        scene.render.engine = 'BLENDER_EEVEE'


# ----------------------------------------------------------------------
# 4. Hero camera + render
# ----------------------------------------------------------------------
def building_bounds():
    mn = mathutils.Vector((1e18, 1e18, 1e18))
    mx = mathutils.Vector((-1e18, -1e18, -1e18))
    found = False
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        found = True
        for c in o.bound_box:
            w = o.matrix_world @ mathutils.Vector(c)
            for i in range(3):
                mn[i] = min(mn[i], w[i])
                mx[i] = max(mx[i], w[i])
    if not found:
        return mathutils.Vector((0, 0, 0)), mathutils.Vector((1, 1, 1))
    return mn, mx


def hero_render(out_png):
    scene = bpy.context.scene
    mn, mx = building_bounds()
    center = (mn + mx) / 2
    size = (mx - mn)
    reach = max(size.x, size.y, size.z)

    cam = bpy.data.objects.get("HeroCam")
    if cam is None:
        cd = bpy.data.cameras.new("HeroCam")
        cam = bpy.data.objects.new("HeroCam", cd)
        scene.collection.objects.link(cam)
    cam.data.lens = 45
    cam.data.clip_start = 10.0
    cam.data.clip_end = reach * 20

    # 3/4 view: back-right and slightly above mid-height.
    cam.location = center + mathutils.Vector((reach * 1.15, -reach * 1.55, reach * 0.35))
    look = center - cam.location
    cam.rotation_euler = look.to_track_quat('-Z', 'Y').to_euler()
    scene.camera = cam

    scene.render.resolution_x = 1280
    scene.render.resolution_y = 900
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    scene.render.filepath = out_png
    bpy.ops.render.render(write_still=True)
    return out_png


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------
def resolve_root():
    if bpy.data.filepath:
        return os.path.dirname(bpy.data.filepath)
    try:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    except NameError:
        return os.getcwd()


def main():
    root = resolve_root()

    touched = polish_materials()
    print(f"[polish] materials tuned: {len(touched)}")

    build_lighting()
    print("[polish] lighting rig rebuilt")

    render_path = os.path.join(root, "Renders", "polished_hero.png")
    hero_render(render_path)
    print("[polish] rendered:", render_path)

    # Save a POLISHED copy without clobbering the currently open file.
    out_blend = os.path.join(root, "Evacuaide_Building_POLISHED.blend")
    bpy.ops.wm.save_as_mainfile(filepath=out_blend, copy=True)
    print("[polish] saved:", out_blend)
    print("[polish] DONE")


if __name__ == "__main__":
    main()
