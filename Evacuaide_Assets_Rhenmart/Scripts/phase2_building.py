"""
EVACUAIDE - Phase 2: Blueprint Office Building Generator
========================================================
Rebuilds the 5-floor EVACUAIDE office tower that matches the evacuation-map
blueprint (Floors 1-5) exactly. The authoritative room layout, stairwells,
elevators, windows, hazards and per-floor materials are captured in the
sibling data file:

    building_layout.json

That JSON is the single source of truth: it was extracted from the approved
Blender scene, so regenerating from it reproduces the building 1:1. Editing
the layout is done by editing the JSON (or re-exporting from Blender), not by
hand-tuning code here.

Run inside Blender (Scripting -> Run Script) or headless:
    blender --background --python phase2_building.py

Produces, in ../Building relative to this script:
    OfficeBuilding_5F.fbx   full detailed 5-floor building
    and one Floor_0N.fbx per floor in ../Floors

Blueprint layout summary (matches the SVG evac maps):
  Footprint 30 x 20 units, 5 floors x 3 units tall.
  Stairwell A (front-left) + Stairwell B (front-right) on every floor.
  Central elevator bank. Perimeter curtain windows on front + back.
  F1  : Security Office, Reception, Restrooms M/F, Janitor closets,
        Main Exit (front) + Emergency Exit (rear), Elevator bank.
  F2-4: Manager Office, Conference Room, Open Office (workstations),
        Pantry, Storage, Restrooms, twin emergency exits.
  F5  : Executive Office, Board Room, Exec Restroom, Pantry, Storage,
        Roof Access, twin emergency exits.
  Hazards baked per floor: bookshelf, glass partition, electrical panel,
  ceiling debris (each with an emissive hazard-glow marker).

Conventions: 1 Blender unit = 1 m. Export scale 1.0 (already metric).
"""

import bpy
import json
import os
import sys

# ----------------------------------------------------------------------
# PATHS
# ----------------------------------------------------------------------
try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = os.path.dirname(bpy.data.filepath) or os.getcwd()
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

LAYOUT_JSON = os.path.join(SCRIPT_DIR, "building_layout.json")

ROOT = os.path.dirname(SCRIPT_DIR)
BUILDING_DIR = os.path.join(ROOT, "Building")
FLOORS_DIR = os.path.join(ROOT, "Floors")
os.makedirs(BUILDING_DIR, exist_ok=True)
os.makedirs(FLOORS_DIR, exist_ok=True)

EXPORT_SCALE = 1.0  # layout is already in metres

# Collection each object is filed under, keyed by name prefix/substring.
# Order matters: the first matching token wins.
COLLECTION_RULES = [
    ("EQ_", "Equipment"),
    ("EVAC", "EvacMarkers"), ("Sign", "Signage"),
    ("_Book", "Hazards"), ("_Glass_", "Hazards"), ("_Elec", "Hazards"),
    ("_Debris", "Hazards"), ("_Ceil_", "Hazards"), ("_Haz", "Hazards"),
    ("_Wall", "Building"), ("_Win", "Building"), ("_Slab", "Building"),
    ("_Ceiling", "Building"),
    ("_Stair", "Building"), ("_Elev", "Building"),
    ("Exit", "Building"),
]
DEFAULT_COLLECTION = "Rooms"


# ----------------------------------------------------------------------
# SCENE + MATERIAL HELPERS
# ----------------------------------------------------------------------
def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.curves):
        for b in list(block):
            if b.users == 0:
                block.remove(b)


def get_collection(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


def build_material(name, spec):
    """Create a Principled BSDF material from a JSON material spec."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF") or nt.nodes.new("ShaderNodeBsdfPrincipled")
    r, g, b = spec["base"]
    alpha = spec.get("alpha", 1.0)
    bsdf.inputs["Base Color"].default_value = (r, g, b, alpha)
    bsdf.inputs["Roughness"].default_value = spec.get("rough", 0.7)
    bsdf.inputs["Metallic"].default_value = spec.get("metal", 0.0)
    if "Alpha" in bsdf.inputs:
        bsdf.inputs["Alpha"].default_value = alpha
    er, eg, eb = spec.get("emit", [0, 0, 0])
    if "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = (er, eg, eb, 1.0)
    if "Emission Strength" in bsdf.inputs:
        bsdf.inputs["Emission Strength"].default_value = spec.get("emit_str", 0.0)
    if alpha < 1.0:
        mat.blend_method = 'BLEND'
    mat.diffuse_color = (r, g, b, alpha)
    return mat


def collection_for(name):
    for token, coll in COLLECTION_RULES:
        if token in name:
            return coll
    return DEFAULT_COLLECTION


# ----------------------------------------------------------------------
# GEOMETRY
# ----------------------------------------------------------------------
def make_box(name, center, dims, mat, coll):
    """Axis-aligned cuboid from center + full dimensions."""
    # size=2 => the base cube spans -1..1 (half-extent 1.0), so scaling by
    # dims/2 yields the requested FULL dimensions. (size=1 would halve them.)
    bpy.ops.mesh.primitive_cube_add(size=2, location=center)
    o = bpy.context.active_object
    o.name = name
    o.scale = (dims[0] / 2.0, dims[1] / 2.0, dims[2] / 2.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat:
        o.data.materials.append(mat)
    for c in list(o.users_collection):
        c.objects.unlink(o)
    coll.objects.link(o)
    return o


# ----------------------------------------------------------------------
# EXPORT
# ----------------------------------------------------------------------
def export_fbx(objects, filepath):
    bpy.ops.object.select_all(action='DESELECT')
    objects = [o for o in objects if o and o.name in bpy.data.objects]
    for o in objects:
        o.select_set(True)
    if objects:
        bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.fbx(
        filepath=filepath, use_selection=True,
        apply_scale_options='FBX_SCALE_ALL', global_scale=EXPORT_SCALE,
        object_types={'MESH'}, mesh_smooth_type='FACE',
        bake_space_transform=True, axis_forward='-Z', axis_up='Y',
    )
    print("Exported:", filepath)


# ----------------------------------------------------------------------
# BUILD
# ----------------------------------------------------------------------
def load_layout():
    with open(LAYOUT_JSON, "r") as f:
        return json.load(f)


def build_from_layout(data):
    # materials first
    materials = {}
    for name, spec in data["materials"].items():
        materials[name] = build_material(name, spec)

    # ensure collections exist
    for _, coll in COLLECTION_RULES:
        get_collection(coll)
    get_collection(DEFAULT_COLLECTION)

    floor_objects = {f: [] for f in range(1, data["num_floors"] + 1)}
    for rec in data["objects"]:
        name = rec["n"]
        mat = materials.get(rec["m"]) if rec["m"] else None
        coll = get_collection(collection_for(name))
        o = make_box(name, rec["c"], rec["d"], mat, coll)
        # The "DO NOT USE" elevator X is two diagonal strokes ("_a"/"_b") that
        # share a center; rotate them +/-45 deg about Y so they actually form
        # an X on the door face (without this they overlap into one flat bar).
        if "_ElevX" in name and name.endswith(("_a", "_b")):
            import math as _m
            o.rotation_euler = (0.0, _m.radians(45 if name.endswith("_a") else -45), 0.0)
        f = floor_of(name, data["num_floors"])
        if f:
            floor_objects[f].append(o)
    return floor_objects


def floor_of(name, num_floors):
    """Resolve the floor index for an object from either an 'F<n>_' prefix
    (building/hazards) or an '_F<n>' suffix token (equipment/signage)."""
    for f in range(1, num_floors + 1):
        if name.startswith(f"F{f}_") or f"_F{f}" in name:
            return f
    return None


def add_lighting():
    """Preview key light (not exported into geometry)."""
    if bpy.data.objects.get("Sun_Key") is None:
        ld = bpy.data.lights.new("Sun_Key", type='SUN')
        ld.energy = 3.0
        obj = bpy.data.objects.new("Sun_Key", ld)
        obj.rotation_euler = (0.9, 0.2, 0.5)
        bpy.context.scene.collection.objects.link(obj)


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------
def main():
    if not os.path.exists(LAYOUT_JSON):
        raise SystemExit(
            "building_layout.json not found next to this script. It is the "
            "source of truth for the blueprint layout; regenerate it by "
            "exporting from the approved Blender scene."
        )
    clear_scene()
    data = load_layout()
    floor_objects = build_from_layout(data)
    add_lighting()

    # per-floor FBX
    for f, objs in floor_objects.items():
        if objs:
            export_fbx(objs, os.path.join(FLOORS_DIR, f"Floor_{f:02d}.fbx"))

    # Full building SHELL FBX. NOTE: this writes a SEPARATE filename
    # (OfficeBuilding_5F_shell.fbx), NOT the canonical OfficeBuilding_5F.fbx.
    # The canonical file is owned solely by phase9_export_glb (the fully
    # decorated + facade + interior + exterior + evac-center export). Keeping
    # them separate prevents this shell-only pass from clobbering the final
    # Unity asset when phase2 is run standalone (e.g. by a verify script).
    all_objs = [o for o in bpy.data.objects if o.type == 'MESH']
    export_fbx(all_objs, os.path.join(BUILDING_DIR, "OfficeBuilding_5F_shell.fbx"))

    print("DONE. Rebuilt blueprint building:",
          sum(len(v) for v in floor_objects.values()), "objects across",
          data["num_floors"], "floors")


if __name__ == "__main__":
    main()
