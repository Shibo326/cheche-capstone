"""
EVACUAIDE - Phase 4: Interactive Emergency Equipment
====================================================
Run in Blender or headless:
    blender --background --python phase4_equipment.py

Each object is grab-scale for Meta Quest hand tracking and includes a
"GrabPoint" EMPTY at the natural grip location for Unity XR Interaction
Toolkit socket/attach alignment. Object origin sits at its base.

Outputs to ../Equipment:
    Flashlight.fbx
    EmergencyBag.fbx
    FirstAidKit.fbx
    FireExtinguisher.fbx
"""

import bpy
import math
import os

EXPORT_SCALE = 0.01

try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = os.path.dirname(bpy.data.filepath) or os.getcwd()
ROOT = os.path.dirname(SCRIPT_DIR)
EQ_DIR = os.path.join(ROOT, "Equipment")
os.makedirs(EQ_DIR, exist_ok=True)


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for b in list(bpy.data.meshes):
        if b.users == 0:
            bpy.data.meshes.remove(b)


def get_mat(name, rgba, rough=0.6, emit=0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = rgba
        bsdf.inputs["Roughness"].default_value = rough
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = rgba
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = emit
    mat.diffuse_color = rgba
    return mat


def box(name, size, loc, rot=(0, 0, 0), mat=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    o.rotation_euler = rot
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat:
        o.data.materials.append(mat)
    return o


def cyl(name, r, h, loc, rot=(0, 0, 0), mat=None, verts=16):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, vertices=verts, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.rotation_euler = rot
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat:
        o.data.materials.append(mat)
    return o


def join_as(name, objs):
    objs = [o for o in objs if o and o.name in bpy.data.objects]
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    j = bpy.context.active_object
    j.name = name
    return j


def add_grabpoint(loc, parent):
    bpy.ops.object.empty_add(type='ARROWS', location=loc)
    e = bpy.context.active_object
    e.name = "GrabPoint"
    e.empty_display_size = 3
    e.parent = parent
    return e


def export_group(objs, filepath):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(
        filepath=filepath, use_selection=True,
        apply_scale_options='FBX_SCALE_ALL', global_scale=EXPORT_SCALE,
        object_types={'MESH', 'EMPTY'}, mesh_smooth_type='FACE',
        bake_space_transform=True, axis_forward='-Z', axis_up='Y',
    )
    print("Exported:", filepath)


# --------------------------- equipment (sizes in cm) ---------------------------
def flashlight():
    body_m = get_mat("Mat_FlashBody", (0.15, 0.15, 0.17, 1), rough=0.5)
    lens_m = get_mat("Mat_FlashLens", (1.0, 0.95, 0.7, 1), emit=3.0)
    parts = [
        cyl("fl_body", 2.5, 14, (0, 0, 7), (0, 0, 0), body_m),
        cyl("fl_head", 3.5, 4, (0, 0, 16), (0, 0, 0), body_m),
        cyl("fl_lens", 3.0, 1, (0, 0, 18.5), (0, 0, 0), lens_m),
    ]
    obj = join_as("Flashlight", parts)
    gp = add_grabpoint((0, 0, 7), obj)          # grip on body
    # light anchor empty at lens
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 19))
    la = bpy.context.active_object
    la.name = "LightAnchor"
    la.parent = obj
    return [obj, gp, la]


def emergency_bag():
    red = get_mat("Mat_BagRed", (0.75, 0.12, 0.12, 1), rough=0.7)
    strap = get_mat("Mat_Strap", (0.1, 0.1, 0.1, 1))
    white = get_mat("Mat_White", (0.95, 0.95, 0.95, 1))
    parts = [
        box("bag_body", (30, 18, 42), (0, 0, 21), mat=red),
        box("bag_pocket", (24, 6, 20), (0, 12, 15), mat=red),
        box("bag_strap_l", (6, 4, 40), (-9, -10, 22), (0.2, 0, 0), strap),
        box("bag_strap_r", (6, 4, 40), (9, -10, 22), (0.2, 0, 0), strap),
        box("bag_cross_v", (4, 1, 14), (0, 9.5, 30), mat=white),
        box("bag_cross_h", (14, 1, 4), (0, 9.5, 30), mat=white),
    ]
    obj = join_as("EmergencyBag", parts)
    gp = add_grabpoint((0, -4, 40), obj)        # top handle grip
    return [obj, gp]


def first_aid_kit():
    white = get_mat("Mat_KitWhite", (0.95, 0.95, 0.95, 1), rough=0.5)
    red = get_mat("Mat_KitRed", (0.85, 0.1, 0.1, 1))
    parts = [
        box("kit_body", (25, 16, 18), (0, 0, 9), mat=white),
        box("kit_handle", (10, 3, 4), (0, 0, 19), mat=white),
        box("kit_cross_v", (4, 1, 12), (0, -8.2, 9), mat=red),
        box("kit_cross_h", (12, 1, 4), (0, -8.2, 9), mat=red),
        box("kit_latch", (5, 2, 3), (0, 8.2, 4), mat=red),
    ]
    obj = join_as("FirstAidKit", parts)
    gp = add_grabpoint((0, 0, 20), obj)         # handle grip
    return [obj, gp]


def fire_extinguisher():
    red = get_mat("Mat_ExtRed", (0.8, 0.08, 0.08, 1), rough=0.4)
    metal = get_mat("Mat_ExtMetal", (0.6, 0.62, 0.65, 1), rough=0.3)
    black = get_mat("Mat_ExtBlack", (0.08, 0.08, 0.08, 1))
    parts = [
        cyl("ext_body", 7, 36, (0, 0, 18), (0, 0, 0), red),
        cyl("ext_top", 5, 6, (0, 0, 38), (0, 0, 0), red),
        cyl("ext_valve", 2, 6, (0, 0, 43), (0, 0, 0), metal),
        box("ext_handle", (10, 4, 3), (0, 0, 47), mat=black),
        cyl("ext_gauge", 2.5, 1.5, (5, 0, 40), (math.radians(90), 0, 0), metal),
        cyl("ext_nozzle", 1.2, 14, (8, 0, 25), (0, math.radians(70), 0), black),
    ]
    obj = join_as("FireExtinguisher", parts)
    gp = add_grabpoint((0, 0, 45), obj)         # handle grip
    return [obj, gp]


EQUIPMENT = [
    ("Flashlight", flashlight),
    ("EmergencyBag", emergency_bag),
    ("FirstAidKit", first_aid_kit),
    ("FireExtinguisher", fire_extinguisher),
]


def main():
    for fname, builder in EQUIPMENT:
        clear_scene()
        objs = builder()
        export_group(objs, os.path.join(EQ_DIR, fname + ".fbx"))
    print("DONE equipment:", len(EQUIPMENT))


if __name__ == "__main__":
    main()
