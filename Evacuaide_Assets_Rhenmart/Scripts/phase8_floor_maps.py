"""
EVACUAIDE - Phase 8: Top-Down Floor-Plan Map Renders
=====================================================
Renders a clean top-down "you-are-here" floor plan PNG for each of the 5
floors, straight from the canonical building. For every floor it hides that
floor's ceiling + the exterior shell (perimeter walls/windows) so the interior
room layout, stairwells, elevator core and emissive evac signage read like the
blueprint maps.

Headless usage:
    blender --background "<canonical.blend>" --python phase8_floor_maps.py
or standalone (loads the .blend itself):
    blender --background --python phase8_floor_maps.py

Outputs PNGs to ../Renders/FloorMaps/Floor_0N_Map.png
"""

import bpy
import os
import sys

try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = os.path.dirname(bpy.data.filepath) or os.getcwd()

ROOT = os.path.dirname(SCRIPT_DIR)
BLEND = os.path.join(ROOT, "Evacuaide_Phase1_Building.blend")
OUT_DIR = os.path.join(ROOT, "Renders", "FloorMaps")
os.makedirs(OUT_DIR, exist_ok=True)

FOOTPRINT_X, FOOTPRINT_Y = 30.0, 20.0
FLOOR_H = 3.0
NUM_FLOORS = 5

# Per-floor accent tint for the map background (matches the evac-map + facade
# color coding: F1 grey / F2 blue / F3 green / F4 gold / F5 maroon).
FLOOR_TINT = {
    1: (0.06, 0.06, 0.07),
    2: (0.04, 0.06, 0.10),
    3: (0.04, 0.08, 0.05),
    4: (0.09, 0.07, 0.03),
    5: (0.09, 0.04, 0.04),
}

# Exterior shell + ceiling tokens to hide so we see inside from the top. Also
# hide the whole exterior campus + facade so the plan reads like a blueprint.
SHELL_TOKENS = ["_Ceiling", "_Wall_F", "_Wall_B", "_Wall_L", "_Wall_R",
                "_Win_F", "_Win_B", "_Ceil_Debris", "_Ceil_Glow",
                "_Hdr", "EXT_", "FAC_", "EQ_", "PantryUpper"]


def ensure_scene_loaded():
    # If launched without the .blend, open it now.
    if not bpy.data.objects.get("F1_Slab") and os.path.exists(BLEND):
        bpy.ops.wm.open_mainfile(filepath=BLEND)


def object_floor(name):
    for f in range(1, NUM_FLOORS + 1):
        if name.startswith(f"F{f}_") or f"_F{f}" in name:
            return f
    return None


def setup_render():
    scene = bpy.context.scene
    scene.render.image_settings.file_format = 'PNG'
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1100
    scene.render.film_transparent = False
    # Prefer EEVEE for speed; fall back to whatever is available.
    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            scene.render.engine = eng
            break
        except TypeError:
            continue
    # world background: dark base; per-floor tint applied in render_floor so
    # emissive evac signage + routes pop and each map is color-coded.
    if scene.world is None:
        scene.world = bpy.data.worlds.new("MapWorld")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.06, 0.06, 0.07, 1)
        bg.inputs[1].default_value = 1.0


def boost_evac_emission():
    """Make evac routes / exits / equipment read strongly on the plan."""
    for mn, strength in (("Mat_Arrow", 4.0), ("Mat_ExitGreen", 5.0),
                         ("Mat_ExitSign", 5.0), ("Mat_HazardGlow", 3.0)):
        m = bpy.data.materials.get(mn)
        if m and m.use_nodes:
            b = m.node_tree.nodes.get("Principled BSDF")
            if b and "Emission Strength" in b.inputs:
                b.inputs["Emission Strength"].default_value = strength


def make_top_camera():
    cam = bpy.data.objects.get("MapCam")
    if cam is None:
        cd = bpy.data.cameras.new("MapCam")
        cam = bpy.data.objects.new("MapCam", cd)
        bpy.context.scene.collection.objects.link(cam)
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = max(FOOTPRINT_X, FOOTPRINT_Y) + 4
    cam.rotation_euler = (0, 0, 0)  # look straight down -Z
    bpy.context.scene.camera = cam
    return cam


def add_fill_light():
    if bpy.data.objects.get("MapFill") is None:
        ld = bpy.data.lights.new("MapFill", 'SUN')
        ld.energy = 5.0
        o = bpy.data.objects.new("MapFill", ld)
        o.rotation_euler = (0.15, 0.1, 0.0)  # near-vertical for even plan lighting
        bpy.context.scene.collection.objects.link(o)


def render_floor(f, cam):
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    for o in meshes:
        on_floor = (object_floor(o.name) == f)
        is_shell = any(tok in o.name for tok in SHELL_TOKENS)
        o.hide_render = (not on_floor) or is_shell
    # per-floor background tint
    scene = bpy.context.scene
    bg = scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (*FLOOR_TINT.get(f, (0.06, 0.06, 0.07)), 1)
    z = (f - 1) * FLOOR_H + 1.5
    cam.location = (0, 0, z + 30)
    scene.render.filepath = os.path.join(OUT_DIR, f"Floor_{f:02d}_Map.png")
    bpy.ops.render.render(write_still=True)
    print("Rendered:", scene.render.filepath)


def main():
    ensure_scene_loaded()
    setup_render()
    boost_evac_emission()
    add_fill_light()
    cam = make_top_camera()
    for f in range(1, NUM_FLOORS + 1):
        render_floor(f, cam)
    print("DONE. Floor maps in", OUT_DIR)


if __name__ == "__main__":
    main()
