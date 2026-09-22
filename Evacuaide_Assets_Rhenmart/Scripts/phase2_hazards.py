"""
EVACUAIDE - PHASE 2: Hazard Objects
===================================
Adds all earthquake hazards in exact blueprint positions, with emissive red
hazard materials for VR visibility. Runs after phase1_building.py.

Hazard placements (STRICT per blueprint):
  FLOOR 1:
    - Falling Bookshelf   -> Security Office (left and right)
    - Electrical Panel    -> near Elevator Bank
    - Glass Partition     -> Reception Desk area
    - Debris Zone         -> ceiling above Main Lobby center
  FLOORS 2-4:
    - Falling Bookshelf   -> near W1, W5, W10 workstations
    - Electrical Panel    -> near Stairwell B (right side)
    - Glass Partition     -> between Manager Office and Open Office
    - Ceiling Tile debris -> above W6, W7 workstations
    - Filing Cabinet      -> Storage Room
  FLOOR 5:
    - Falling Bookshelf   -> Executive Office (left wall)
    - Glass Partition     -> Board Room glass wall
    - Electrical Panel    -> near Elevator Bank
    - Ceiling Tile debris -> above Board Room center

Materials: hazard zones red emissive (#FF2222, emit=2.0).
Units: meters. Blender 5.2.2, pure bpy.
"""
import bpy, math

FLOOR_H = 3.0

def _srgb(c): return c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4
def hex_rgb(h):
    h=h.lstrip("#"); return tuple(_srgb(int(h[i:i+2],16)/255.0) for i in (0,2,4))

def mat_emissive(name, hexstr, strength):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes=True
    b=m.node_tree.nodes.get("Principled BSDF")
    rgb=hex_rgb(hexstr)
    if b:
        b.inputs["Base Color"].default_value=(*rgb,1.0)
        if "Emission Color" in b.inputs: b.inputs["Emission Color"].default_value=(*rgb,1.0)
        if "Emission Strength" in b.inputs: b.inputs["Emission Strength"].default_value=strength
    return m

def mat_solid(name, hexstr, rough=0.7, metal=0.0):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes=True
    b=m.node_tree.nodes.get("Principled BSDF")
    rgb=hex_rgb(hexstr)
    if b:
        b.inputs["Base Color"].default_value=(*rgb,1.0)
        b.inputs["Roughness"].default_value=rough
        b.inputs["Metallic"].default_value=metal
    return m

def get_collection(name, parent=None):
    c=bpy.data.collections.get(name)
    if c is None:
        c=bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c

def box(name, size, loc, mat, coll):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    ob=bpy.context.active_object; ob.name=name; ob.scale=size
    if mat: ob.data.materials.append(mat)
    for c in list(ob.users_collection): c.objects.unlink(ob)
    coll.objects.link(ob)
    return ob

# hazard glow marker (thin red emissive slab tagging the hazard zone)
def hazard_marker(name, loc, coll, mat_glow, size=(1.0,1.0,0.05)):
    return box(name, size, loc, mat_glow, coll)

def build_hazards():
    glow   = mat_emissive("Mat_HazardGlow", "#FF2222", 2.0)
    wood   = mat_solid("Mat_Bookshelf", "#5A3A1A", 0.7)
    glass  = mat_solid("Mat_HazGlass", "#8FB8CC", 0.1)
    panel  = mat_solid("Mat_ElecPanel", "#C0C0C0", 0.4, 0.7)
    metal  = mat_solid("Mat_Cabinet", "#7A7E82", 0.5, 0.6)
    debris = mat_solid("Mat_Debris", "#6B6B6B", 0.95)

    root = get_collection("Evacuaide_Hazards")
    count = 0

    def bookshelf(tag, x, y, base, coll):
        nonlocal count
        box(f"{tag}_Shelf", (0.4,1.6,2.0), (x,y,base+1.0), wood, coll)
        hazard_marker(f"{tag}_Glow", (x,y,base+0.06), coll, glow, (1.2,2.0,0.05))
        count += 2

    def elec_panel(tag, x, y, base, coll):
        nonlocal count
        box(f"{tag}_Panel", (0.15,0.8,1.2), (x,y,base+1.3), panel, coll)
        hazard_marker(f"{tag}_Glow", (x,y,base+0.06), coll, glow, (0.9,1.0,0.05))
        count += 2

    def glass_part(tag, x, y, base, coll, span=3.0, axis='x'):
        nonlocal count
        size=(span,0.1,2.0) if axis=='x' else (0.1,span,2.0)
        box(f"{tag}_Glass", size, (x,y,base+1.0), glass, coll)
        gsize=(span,0.6,0.05) if axis=='x' else (0.6,span,0.05)
        hazard_marker(f"{tag}_Glow", (x,y,base+0.06), coll, glow, gsize)
        count += 2

    def debris_ceiling(tag, x, y, base, coll, span=(3.0,3.0)):
        nonlocal count
        box(f"{tag}_Debris", (span[0],span[1],0.25), (x,y,base+FLOOR_H-0.4), debris, coll)
        hazard_marker(f"{tag}_Glow", (x,y,base+FLOOR_H-0.15), coll, glow, (span[0],span[1],0.05))
        count += 2

    def filing_cabinet(tag, x, y, base, coll):
        nonlocal count
        box(f"{tag}_Cabinet", (0.6,0.5,1.4), (x,y,base+0.7), metal, coll)
        hazard_marker(f"{tag}_Glow", (x,y,base+0.06), coll, glow, (0.9,0.8,0.05))
        count += 2

    # ---------------- FLOOR 1 ----------------
    c1 = get_collection("Hazards_F1", root); base=0.0
    # bookshelf in security offices (upper-left & lower-left)
    bookshelf("F1_Book_SecU", -13.5, 6.0, base, c1)
    bookshelf("F1_Book_SecL", -13.5, -6.0, base, c1)
    # electrical panel near elevator bank (elevators at center ~y6.5)
    elec_panel("F1_Elec", 1.6, 6.5, base, c1)
    # glass partition at reception desk area
    glass_part("F1_Glass", -5.8, 4.5, base, c1, span=4.0, axis='y')
    # debris above main lobby center
    debris_ceiling("F1_Debris", 0.0, -1.0, base, c1, span=(4.0,4.0))

    # ---------------- FLOORS 2-4 ----------------
    # workstation ref positions from phase1: rows_y=[3.5,0,-3.5], cols_x=[-6.5,-4,-1.5,1,3.5]
    # W1=(-6.5,3.5) top-left, W5=(-4,0) mid, W10=(-4,-3.5) approx, W6/W7 middle row
    for f in (2,3,4):
        cf = get_collection(f"Hazards_F{f}", root); b=(f-1)*FLOOR_H
        # bookshelf near W1, W5, W10
        bookshelf(f"F{f}_Book_W1", -6.5, 4.6, b, cf)
        bookshelf(f"F{f}_Book_W5", -4.0, 1.1, b, cf)
        bookshelf(f"F{f}_Book_W10", -4.0, -4.6, b, cf)
        # electrical panel near Stairwell B (right side, x=12)
        elec_panel(f"F{f}_Elec", 10.3, -3.0, b, cf)
        # glass partition between Manager Office (y5..9) and Open Office
        glass_part(f"F{f}_Glass", 0.0, 4.7, b, cf, span=6.0, axis='x')
        # ceiling tile debris above W6,W7 (middle row center)
        debris_ceiling(f"F{f}_Ceil", -0.25, 0.0, b, cf, span=(3.0,2.0))
        # filing cabinet in storage room (x6..9.5, y-9..-3)
        filing_cabinet(f"F{f}_File", 8.0, -6.0, b, cf)

    # ---------------- FLOOR 5 ----------------
    c5 = get_collection("Hazards_F5", root); b=(5-1)*FLOOR_H
    # bookshelf executive office left wall (exec office x-15..-6, y2..9)
    bookshelf("F5_Book_Exec", -14.0, 5.5, b, c5)
    # glass partition board room glass wall (board room x-15..-6, y-9..-1)
    glass_part("F5_Glass", -6.0, -5.0, b, c5, span=6.0, axis='y')
    # electrical panel near elevator bank (center, y5.5)
    elec_panel("F5_Elec", 1.6, 5.5, b, c5)
    # ceiling tile debris above board room center
    debris_ceiling("F5_Ceil", -10.5, -5.0, b, c5, span=(4.0,4.0))

    bpy.context.view_layer.update()
    return count

if __name__ == "__main__":
    n = build_hazards()
    total = len(bpy.context.scene.objects)
    print("="*60)
    print(f"PHASE 2 COMPLETE - {n} hazard objects created (scene total {total})")
    print("="*60)
