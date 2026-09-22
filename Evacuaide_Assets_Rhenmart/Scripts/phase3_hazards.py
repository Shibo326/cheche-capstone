"""
EVACUAIDE - Phase 3: Earthquake Hazard Objects
===============================================
Run in Blender or headless:
    blender --background --python phase3_hazards.py

Each hazard exports ONE .fbx containing two meshes:
    <Name>_Pre   (pre-earthquake state)
    <Name>_Post  (post-earthquake state)
Unity can enable/disable each child to swap states at runtime.

Outputs to ../Hazards:
    Bookshelf_Fall.fbx
    CeilingTile_Crack.fbx
    GlassPartition_Break.fbx
    FilingCabinet_Topple.fbx
    ElectricalPanel_Spark.fbx
"""

import bpy
import math
import os
import random
import sys

EXPORT_SCALE = 0.01

try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = os.path.dirname(bpy.data.filepath) or os.getcwd()
# Share the central material library so hazard colors match the SVG map palette.
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
import evac_art as art

ROOT = os.path.dirname(SCRIPT_DIR)
HAZ_DIR = os.path.join(ROOT, "Hazards")
os.makedirs(HAZ_DIR, exist_ok=True)


# --------------------------- helpers ---------------------------
def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for b in list(bpy.data.meshes):
        if b.users == 0:
            bpy.data.meshes.remove(b)


def get_mat(name, rgba, rough=0.8, emit=0.0):
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


def join_as(name, objs):
    objs = [o for o in objs if o and o.name in bpy.data.objects]
    if not objs:
        return None
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    j = bpy.context.active_object
    j.name = name
    return j


def export_group(objs, filepath):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        if o and o.name in bpy.data.objects:
            o.select_set(True)
    if objs:
        bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(
        filepath=filepath, use_selection=True,
        apply_scale_options='FBX_SCALE_ALL', global_scale=EXPORT_SCALE,
        object_types={'MESH', 'EMPTY'}, mesh_smooth_type='FACE',
        bake_space_transform=True, axis_forward='-Z', axis_up='Y',
    )
    print("Exported:", filepath)


# --------------------------- hazards ---------------------------
def bookshelf():
    wood = get_mat("Mat_Wood", (0.40, 0.26, 0.13, 1))
    book = get_mat("Mat_Book", (0.6, 0.2, 0.2, 1))

    def make_shelf(offset, rot, scatter):
        parts = []
        px, pz = offset
        # frame
        parts.append(box("bs_side_l", (10, 40, 200), (px - 55, 0, pz + 100), rot, wood))
        parts.append(box("bs_side_r", (10, 40, 200), (px + 55, 0, pz + 100), rot, wood))
        for i in range(4):
            parts.append(box(f"bs_shelf_{i}", (110, 40, 8), (px, 0, pz + 20 + i * 55), rot, wood))
        # books
        for i in range(4):
            for b in range(5):
                bx = px - 40 + b * 20 + (random.uniform(-40, 40) if scatter else 0)
                bz = pz + 30 + i * 55 + (random.uniform(0, 30) if scatter else 0)
                brot = (0, random.uniform(-1.2, 1.2), 0) if scatter else rot
                parts.append(box(f"bk_{i}_{b}", (15, 25, 30), (bx, 0, bz), brot, book))
        return parts

    pre = join_as("Bookshelf_Fall_Pre", make_shelf((0, 0), (0, 0, 0), False))
    # post: toppled forward ~85 deg, books scattered on floor
    post_parts = make_shelf((0, 0), (math.radians(85), 0, 0), True)
    post = join_as("Bookshelf_Fall_Post", post_parts)
    post.location.y += 90
    post.location.z = 20
    return [pre, post]


def ceiling_tile():
    tile = art.ceiling_tile()  # shared library material (matches building ceilings)
    pre = box("CeilingTile_Crack_Pre", (120, 120, 4), (0, 0, 0), mat=tile)
    # post: broken into 4 tilted quarter panels, dropped
    parts = []
    for i, (dx, dy) in enumerate([(-30, -30), (30, -30), (-30, 30), (30, 30)]):
        parts.append(box(f"ct_q{i}", (58, 58, 4),
                         (dx, dy, -20 - random.uniform(0, 10)),
                         (random.uniform(-0.4, 0.4), random.uniform(-0.4, 0.4), 0), tile))
    post = join_as("CeilingTile_Crack_Post", parts)
    return [pre, post]


def glass_partition():
    glass = get_mat("Mat_Glass", (0.6, 0.8, 0.9, 0.4), rough=0.1)
    shard = get_mat("Mat_Shard", (0.7, 0.85, 0.95, 0.5), rough=0.1)
    pre = box("GlassPartition_Break_Pre", (300, 6, 200), (0, 0, 100), mat=glass)
    # post: frame stays, shards scattered on floor
    parts = [box("gp_frame_l", (8, 8, 200), (-150, 0, 100), mat=shard),
             box("gp_frame_r", (8, 8, 200), (150, 0, 100), mat=shard),
             box("gp_frame_t", (300, 8, 8), (0, 0, 200), mat=shard)]
    for i in range(14):
        parts.append(box(f"gp_shard_{i}",
                         (random.uniform(10, 40), 4, random.uniform(10, 40)),
                         (random.uniform(-140, 140), random.uniform(-30, 30), random.uniform(2, 8)),
                         (0, 0, random.uniform(-1.5, 1.5)), shard))
    post = join_as("GlassPartition_Break_Post", parts)
    return [pre, post]


def filing_cabinet():
    metal = get_mat("Mat_Metal", (0.55, 0.57, 0.6, 1), rough=0.4)

    def make(rot, drawers_out):
        parts = [box("fc_body", (60, 50, 130), (0, 0, 65), (0, 0, 0), metal)]
        for i in range(3):
            dy = 26 if drawers_out else 0
            parts.append(box(f"fc_drawer_{i}", (54, 45, 30), (0, dy, 30 + i * 40), (0, 0, 0), metal))
        j = join_as("tmp", parts)
        j.rotation_euler = rot
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        return j

    pre = make((0, 0, 0), False)
    pre.name = "FilingCabinet_Topple_Pre"
    post = make((math.radians(88), 0, 0), True)
    post.name = "FilingCabinet_Topple_Post"
    post.location = (0, 65, 30)
    return [pre, post]


def electrical_panel():
    gray = get_mat("Mat_PanelGray", (0.35, 0.37, 0.4, 1), rough=0.5)
    spark = get_mat("Mat_Spark", (1.0, 0.85, 0.2, 1), emit=6.0)
    wire = get_mat("Mat_Wire", (0.1, 0.1, 0.1, 1))
    # pre: closed panel
    pre_parts = [box("ep_box", (60, 20, 90), (0, 0, 45), mat=gray),
                 box("ep_door", (58, 3, 86), (0, -11, 45), mat=gray)]
    pre = join_as("ElectricalPanel_Spark_Pre", pre_parts)
    # post: door ajar, wires + spark point
    post_parts = [box("ep_box2", (60, 20, 90), (0, 0, 45), mat=gray),
                  box("ep_door2", (58, 3, 86), (-30, -18, 45), (0, 0, math.radians(60)), gray)]
    for i in range(5):
        post_parts.append(box(f"ep_wire_{i}", (2, 12, 2),
                              (-20 + i * 10, -8, 60 + random.uniform(-10, 10)),
                              (random.uniform(-1, 1), 0, 0), wire))
    # red hazard warning strip on the exposed panel (matches map hazard color)
    hazard_m = art.hazard_red()
    post_parts.append(box("ep_hazard_strip", (58, 2, 6), (0, -13, 82), mat=hazard_m))
    spark_pt = box("ElectricalPanel_SparkPoint", (6, 6, 6), (0, -6, 70), mat=spark)
    post = join_as("ElectricalPanel_Spark_Post", post_parts)
    return [pre, post, spark_pt]


HAZARDS = [
    ("Bookshelf_Fall", bookshelf),
    ("CeilingTile_Crack", ceiling_tile),
    ("GlassPartition_Break", glass_partition),
    ("FilingCabinet_Topple", filing_cabinet),
    ("ElectricalPanel_Spark", electrical_panel),
]


def main():
    random.seed(7)  # deterministic output
    for fname, builder in HAZARDS:
        clear_scene()
        objs = builder()
        export_group(objs, os.path.join(HAZ_DIR, fname + ".fbx"))
    print("DONE hazards:", len(HAZARDS))


if __name__ == "__main__":
    main()
