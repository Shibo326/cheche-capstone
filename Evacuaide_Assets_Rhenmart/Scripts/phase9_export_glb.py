"""
EVACUAIDE - Phase 9: Unity Export (GLB + FBX)
=============================================
Exports the canonical detailed building to Unity-ready formats:
  - OfficeBuilding_5F.glb   (glTF binary; keeps PBR + emissive evac signage)
  - OfficeBuilding_5F.fbx   (also re-exported for pipelines that prefer FBX)

GLB is preferred for Unity import here because the evac signage, hazard-glow
and exit markers rely on emissive materials that survive glTF cleanly.

Headless usage:
    blender --background "<canonical.blend>" --python phase9_export_glb.py
or standalone (loads the .blend itself):
    blender --background --python phase9_export_glb.py

Outputs to ../Building/
"""

import bpy
import os

try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = os.path.dirname(bpy.data.filepath) or os.getcwd()

ROOT = os.path.dirname(SCRIPT_DIR)
BLEND = os.path.join(ROOT, "Evacuaide_Phase1_Building.blend")
BUILDING_DIR = os.path.join(ROOT, "Building")
os.makedirs(BUILDING_DIR, exist_ok=True)


def ensure_scene_loaded():
    if not bpy.data.objects.get("F1_Slab") and os.path.exists(BLEND):
        bpy.ops.wm.open_mainfile(filepath=BLEND)


def select_all_meshes():
    # The Unity/VR asset must be the COMPLETE closed building - if an authoring
    # cutaway (phase2e) hid ceilings/front walls, un-hide everything first so the
    # walkthrough geometry is whole regardless of phase order.
    for o in bpy.data.objects:
        if o.type == 'MESH':
            o.hide_set(False)
            o.hide_viewport = False
            o.hide_render = False
    bpy.ops.object.select_all(action='DESELECT')
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    for o in meshes:
        o.select_set(True)
    if meshes:
        bpy.context.view_layer.objects.active = meshes[0]
    return meshes


def export_glb(meshes):
    path = os.path.join(BUILDING_DIR, "OfficeBuilding_5F.glb")
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format='GLB',
        use_selection=True,
        export_apply=True,               # apply modifiers
        export_yup=True,                 # Unity is Y-up
        export_materials='EXPORT',
        export_cameras=False,
        export_lights=False,
    )
    print("Exported GLB:", path, os.path.getsize(path), "bytes")


def export_fbx(meshes):
    path = os.path.join(BUILDING_DIR, "OfficeBuilding_5F.fbx")
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True,
        apply_scale_options='FBX_SCALE_ALL', global_scale=1.0,
        object_types={'MESH'}, mesh_smooth_type='FACE',
        bake_space_transform=True, axis_forward='-Z', axis_up='Y',
    )
    print("Exported FBX:", path, os.path.getsize(path), "bytes")


def main():
    ensure_scene_loaded()
    meshes = select_all_meshes()
    print("Meshes selected for export:", len(meshes))
    export_glb(meshes)
    export_fbx(meshes)
    print("DONE. Unity-ready building exported to", BUILDING_DIR)


if __name__ == "__main__":
    main()
