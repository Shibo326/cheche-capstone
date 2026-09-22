"""
EVACUAIDE - Shared Art / Material Library
=========================================
Central PBR material definitions + helpers so every generator produces
consistent, non-blockout-looking assets. Import from phase scripts:

    from evac_art import pbr, FLOOR_LOOK, add_area_light, BUILDING_NAME

All colors are linear-ish sRGB tuples (r,g,b,a) in 0..1.
"""

import bpy

BUILDING_NAME = "MANILA INNOVATIONS TOWER"


def pbr(name, base, rough=0.7, metal=0.0, emit=None, emit_str=0.0, alpha=1.0):
    """Create/replace a Principled BSDF material with sane PBR inputs."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    if bsdf is None:
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    r, g, b = base[0], base[1], base[2]
    bsdf.inputs["Base Color"].default_value = (r, g, b, alpha)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if "Alpha" in bsdf.inputs:
        bsdf.inputs["Alpha"].default_value = alpha
    if emit is not None:
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (emit[0], emit[1], emit[2], 1)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = emit_str
    if alpha < 1.0:
        mat.blend_method = 'BLEND'
    mat.diffuse_color = (r, g, b, alpha)
    return mat


# Palette: realistic office surfaces, not primary-color blocks.
def wall_mat():      return pbr("Evac_Wall", (0.86, 0.86, 0.83), rough=0.85)
def floor_slab():    return pbr("Evac_FloorSlab", (0.55, 0.55, 0.57), rough=0.9)
def carpet():        return pbr("Evac_Carpet", (0.28, 0.30, 0.36), rough=1.0)
def glass():         return pbr("Evac_Glass", (0.62, 0.80, 0.86), rough=0.05, alpha=0.35)
def metal_dark():    return pbr("Evac_MetalDark", (0.18, 0.19, 0.21), rough=0.35, metal=0.9)
def metal_light():   return pbr("Evac_MetalLight", (0.62, 0.64, 0.67), rough=0.3, metal=0.85)
def wood():          return pbr("Evac_Wood", (0.42, 0.27, 0.14), rough=0.6)
def fabric():        return pbr("Evac_Fabric", (0.20, 0.22, 0.28), rough=0.95)
def accent(rgb):
    # Key on 0..255 rounded channels so visually distinct colors never
    # collide onto one shared material (0.130 vs 0.135 used to both map to 12).
    key = "_".join(str(round(c * 255)) for c in rgb[:3])
    return pbr(f"Evac_Accent_{key}", rgb, rough=0.5)


# --- Structural / environment surfaces --------------------------------
def concrete():      return pbr("Evac_Concrete", (0.62, 0.61, 0.58), rough=0.95)
def ceiling_tile():  return pbr("Evac_CeilTile", (0.90, 0.90, 0.87), rough=0.9)
def grass():         return pbr("Evac_Grass", (0.20, 0.42, 0.16), rough=1.0)
def pavement():      return pbr("Evac_Pavement", (0.52, 0.52, 0.54), rough=0.9)
def curtain_glass(): return pbr("Evac_CurtainGlass", (0.30, 0.52, 0.60), rough=0.08,
                                metal=0.3, alpha=0.72)
def mullion():       return pbr("Evac_Mullion", (0.22, 0.23, 0.25), rough=0.4, metal=0.85)
def facade_spandrel():return pbr("Evac_Spandrel", (0.30, 0.34, 0.40), rough=0.5, metal=0.6)
def roof_surface():  return pbr("Evac_Roof", (0.34, 0.34, 0.36), rough=0.95)


# --- Evacuation-theme emissive signage --------------------------------
# Colors mirror the SVG map palette so 3D signage reads the same as the maps:
#   exit #2E7D32, hazard #D32F2F, stair #1565C0, assembly #F2C200.
def exit_sign_green():
    """Glowing green exit signage / route markers."""
    return pbr("Evac_ExitGreen", (0.18, 0.49, 0.20), rough=0.4,
               emit=(0.18, 0.49, 0.20), emit_str=3.0)


def hazard_red():
    """Emissive red for hazard markers and warning strips."""
    return pbr("Evac_HazardRed", (0.83, 0.18, 0.18), rough=0.4,
               emit=(0.83, 0.18, 0.18), emit_str=2.5)


def stair_blue():
    """Blue stairwell code color (matches step nosings + map stairs)."""
    return pbr("Evac_StairBlue", (0.08, 0.40, 0.75), rough=0.5,
               emit=(0.08, 0.40, 0.75), emit_str=1.5)


def assembly_yellow():
    """Assembly-point yellow, strongly emissive so it reads at a distance."""
    return pbr("Evac_AssemblyYellow", (0.95, 0.76, 0.0), rough=0.4,
               emit=(0.95, 0.76, 0.0), emit_str=3.5)


def emergency_light():
    """Hot white emergency lighting / battery lamp lens."""
    return pbr("Evac_EmergencyLight", (1.0, 0.98, 0.92), rough=0.2,
               emit=(1.0, 0.98, 0.92), emit_str=6.0)


# Per-floor accent stripe color (used on trim, not whole walls).
FLOOR_LOOK = {
    1: (0.20, 0.62, 0.28),   # green - lobby
    2: (0.13, 0.52, 0.85),   # blue
    3: (0.95, 0.55, 0.05),   # orange
    4: (0.55, 0.20, 0.65),   # purple
    5: (0.85, 0.20, 0.18),   # red - executive
}


def add_area_light(name, loc, energy=2000.0, size=400.0):
    light_data = bpy.data.lights.new(name, type='AREA')
    light_data.energy = energy
    light_data.size = size
    obj = bpy.data.objects.new(name, light_data)
    obj.location = loc
    bpy.context.collection.objects.link(obj)
    return obj


def add_text(name, body, loc, size=60, extrude=2.0, mat=None, rot=(1.5708, 0, 0)):
    """Add 3D text (for building signage). rot default faces +Y."""
    curve = bpy.data.curves.new(name, type='FONT')
    curve.body = body
    curve.extrude = extrude / 100.0
    curve.align_x = 'CENTER'
    curve.size = size
    obj = bpy.data.objects.new(name, curve)
    obj.location = loc
    obj.rotation_euler = rot
    bpy.context.collection.objects.link(obj)
    if mat:
        obj.data.materials.append(mat)
    return obj
