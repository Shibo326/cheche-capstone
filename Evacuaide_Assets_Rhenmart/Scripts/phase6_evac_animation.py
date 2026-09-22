"""
EVACUAIDE - Phase 6: Evacuation Path Animations
================================================
Run in Blender or headless:
    blender --background --python phase6_evac_animation.py

For each of 5 floors, animates a glowing green arrow marker traveling from a
room to the nearest stairwell, then down to the ground exit. A camera follows
the marker. 30 fps, 5 s per floor (150 frames). Animation is baked to keyframes
and exported as FBX with baked animation (Unity Animation Clip ready).

Outputs to ../Animations:
    EvacPath_Floor01.fbx ... EvacPath_Floor05.fbx
"""

import bpy
import math
import os

EXPORT_SCALE = 0.01
FPS = 30
SECONDS = 5
TOTAL_FRAMES = FPS * SECONDS  # 150
FLOOR_H = 350.0

try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = os.path.dirname(bpy.data.filepath) or os.getcwd()
ROOT = os.path.dirname(SCRIPT_DIR)
ANIM_DIR = os.path.join(ROOT, "Animations")
os.makedirs(ANIM_DIR, exist_ok=True)


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for b in list(bpy.data.meshes):
        if b.users == 0:
            bpy.data.meshes.remove(b)


def glow_mat():
    mat = bpy.data.materials.get("Mat_EvacGlow") or bpy.data.materials.new("Mat_EvacGlow")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.1, 1.0, 0.2, 1)
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.1, 1.0, 0.2, 1)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 5.0
    mat.diffuse_color = (0.1, 1.0, 0.2, 1)
    return mat


def make_arrow(mat):
    """Low-poly chevron arrow marker pointing +Y."""
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=25, depth=50,
                                    location=(0, 0, 0), rotation=(math.radians(90), 0, 0))
    tip = bpy.context.active_object
    tip.name = "EvacArrow"
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -35, 0))
    tail = bpy.context.active_object
    tail.scale = (12, 20, 12)
    bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.select_all(action='DESELECT')
    tip.select_set(True)
    tail.select_set(True)
    bpy.context.view_layer.objects.active = tip
    bpy.ops.object.join()
    arrow = bpy.context.active_object
    arrow.name = "EvacArrow"
    arrow.data.materials.append(mat)
    return arrow


def floor_path(floor_idx):
    """Return list of (x,y,z) waypoints: room -> stairwell -> ground exit."""
    z_floor = (floor_idx - 1) * FLOOR_H + 30
    # generic room start on this floor -> stairwell (back-right) -> down -> exit
    pts = [
        (-800, -400, z_floor),   # start at a far room
        (-800, 400, z_floor),    # move up the aisle
        (620, 400, z_floor),     # toward stairwell corner
        (620, 500, z_floor),     # enter stairwell
    ]
    # descend the stairwell to ground level
    steps = max(1, floor_idx - 1)
    for s in range(1, steps + 1):
        z = z_floor - (z_floor - 30) * (s / steps)
        pts.append((620, 500 - s * 10, z))
    # ground exit run
    pts.append((620, 0, 30))
    pts.append((-900, 0, 30))    # main exit door
    return pts


def polyline_length(pts):
    total = 0.0
    for a, b in zip(pts, pts[1:]):
        total += math.dist(a, b)
    return total


def point_at(pts, t):
    """Position along polyline at param t in [0,1] + facing yaw."""
    seg = []
    total = polyline_length(pts)
    if total == 0:
        return pts[0], 0.0
    target = t * total
    acc = 0.0
    for a, b in zip(pts, pts[1:]):
        d = math.dist(a, b)
        if acc + d >= target or b is pts[-1]:
            local = (target - acc) / d if d else 0
            local = max(0.0, min(1.0, local))
            pos = tuple(a[i] + (b[i] - a[i]) * local for i in range(3))
            yaw = math.atan2(b[1] - a[1], b[0] - a[0]) - math.radians(90)
            return pos, yaw
        acc += d
    return pts[-1], 0.0


def animate_floor(floor_idx):
    mat = glow_mat()
    arrow = make_arrow(mat)
    pts = floor_path(floor_idx)

    scene = bpy.context.scene
    scene.render.fps = FPS
    scene.frame_start = 1
    scene.frame_end = TOTAL_FRAMES

    # camera follows behind + above the arrow
    bpy.ops.object.camera_add(location=(0, 0, 0))
    cam = bpy.context.active_object
    cam.name = "EvacCam"

    for f in range(1, TOTAL_FRAMES + 1):
        t = (f - 1) / (TOTAL_FRAMES - 1)
        pos, yaw = point_at(pts, t)
        scene.frame_set(f)
        # arrow
        arrow.location = pos
        arrow.rotation_euler = (0, 0, yaw)
        arrow.keyframe_insert("location")
        arrow.keyframe_insert("rotation_euler")
        # pulse scale for "glow" feel (transform only)
        pulse = 1.0 + 0.15 * math.sin(f * 0.5)
        arrow.scale = (pulse, pulse, pulse)
        arrow.keyframe_insert("scale")
        # camera behind & above, looking at arrow
        cam_pos = (pos[0] - 150 * math.sin(yaw), pos[1] - 150 * math.cos(yaw), pos[2] + 200)
        cam.location = cam_pos
        # aim camera at arrow
        dx, dy, dz = pos[0] - cam_pos[0], pos[1] - cam_pos[1], pos[2] - cam_pos[2]
        cam.rotation_euler = (
            math.atan2(math.hypot(dx, dy), -dz) if False else math.radians(65),
            0,
            math.atan2(dy, dx) - math.radians(90),
        )
        cam.keyframe_insert("location")
        cam.keyframe_insert("rotation_euler")

    return [arrow, cam]


def export_anim(objs, filepath):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(
        filepath=filepath, use_selection=True,
        apply_scale_options='FBX_SCALE_ALL', global_scale=EXPORT_SCALE,
        object_types={'MESH', 'CAMERA', 'EMPTY'}, mesh_smooth_type='FACE',
        bake_anim=True, bake_anim_use_all_bones=False,
        bake_anim_use_nla_strips=False, bake_anim_use_all_actions=False,
        bake_anim_force_startend_keying=True, bake_anim_step=1.0,
        axis_forward='-Z', axis_up='Y', bake_space_transform=True,
    )
    print("Exported:", filepath)


def main():
    for idx in range(1, 6):
        clear_scene()
        objs = animate_floor(idx)
        export_anim(objs, os.path.join(ANIM_DIR, f"EvacPath_Floor{idx:02d}.fbx"))
    print("DONE animations: 5")


if __name__ == "__main__":
    main()
