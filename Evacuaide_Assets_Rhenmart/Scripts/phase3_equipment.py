"""
EVACUAIDE - PHASE 3: Emergency Equipment
========================================
Places emergency equipment on ALL floors, per blueprint:
  - First Aid Kit (green cross)  -> mounted on wall near Stairwell A
  - Fire Extinguisher x2 (red)   -> one near each Emergency Exit
  - Emergency Go Bag (orange)    -> near Stairwell B bottom corner
  - Flashlight (yellow)          -> near Emergency Exit right side

Emissive materials for VR visibility:
  First Aid Kit   green  #00FF00 emit 1.5
  Fire Ext.       red    #FF3300 emit 1.5
  Emergency Bag   orange #FF8800 emit 1.5
  Flashlight      yellow #FFFF00 emit 1.5

Units: meters. Blender 5.2.2, pure bpy. Run after phase2.
Anchors: Stairwell A x=-12, Stairwell B x=+12 (front band).
"""
import bpy

FLOOR_H=3.0
STAIR_A_X=-12.0
STAIR_B_X= 12.0
HALF_Y=10.0

def _srgb(c): return c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4
def hex_rgb(h):
    h=h.lstrip("#"); return tuple(_srgb(int(h[i:i+2],16)/255.0) for i in (0,2,4))

def mat_emissive(name, hexstr, strength):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes=True; b=m.node_tree.nodes.get("Principled BSDF"); rgb=hex_rgb(hexstr)
    if b:
        b.inputs["Base Color"].default_value=(*rgb,1.0)
        if "Emission Color" in b.inputs: b.inputs["Emission Color"].default_value=(*rgb,1.0)
        if "Emission Strength" in b.inputs: b.inputs["Emission Strength"].default_value=strength
    return m

def get_collection(name, parent=None):
    c=bpy.data.collections.get(name)
    if c is None:
        c=bpy.data.collections.new(name); (parent or bpy.context.scene.collection).children.link(c)
    return c

def box(name, size, loc, mat, coll):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    ob=bpy.context.active_object; ob.name=name; ob.scale=size
    if mat: ob.data.materials.append(mat)
    for c in list(ob.users_collection): c.objects.unlink(ob)
    coll.objects.link(ob)
    return ob

def cyl(name, r, h, loc, mat, coll):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, vertices=16)
    ob=bpy.context.active_object; ob.name=name
    if mat: ob.data.materials.append(mat)
    for c in list(ob.users_collection): c.objects.unlink(ob)
    coll.objects.link(ob)
    return ob

def build_equipment():
    m_aid  = mat_emissive("Mat_EQ_FirstAid",  "#00FF00", 1.5)
    m_ext  = mat_emissive("Mat_EQ_FireExt",   "#FF3300", 1.5)
    m_bag  = mat_emissive("Mat_EQ_Bag",       "#FF8800", 1.5)
    m_flash= mat_emissive("Mat_EQ_Flashlight","#FFFF00", 1.5)
    m_white= mat_emissive("Mat_EQ_AidBody",   "#F5F5F5", 0.6)

    root=get_collection("Evacuaide_Equipment")
    count=0

    def first_aid(f, x, y, base, coll):
        nonlocal count
        # white box body mounted on wall + green cross face
        box(f"EQ_FirstAid_F{f}_Body", (0.35,0.12,0.35), (x,y,base+1.5), m_white, coll)
        box(f"EQ_FirstAid_F{f}_CrossV", (0.08,0.14,0.22), (x,y-0.02,base+1.5), m_aid, coll)
        box(f"EQ_FirstAid_F{f}_CrossH", (0.22,0.14,0.08), (x,y-0.02,base+1.5), m_aid, coll)
        count+=3

    def fire_ext(tag, x, y, base, coll):
        nonlocal count
        cyl(f"EQ_FireExt_{tag}", 0.12, 0.6, (x,y,base+0.4), m_ext, coll)
        count+=1

    def go_bag(f, x, y, base, coll):
        nonlocal count
        box(f"EQ_GoBag_F{f}", (0.4,0.3,0.5), (x,y,base+0.25), m_bag, coll)
        count+=1

    def flashlight(f, x, y, base, coll):
        nonlocal count
        cyl(f"EQ_Flashlight_F{f}", 0.05, 0.25, (x,y,base+1.2), m_flash, coll)
        count+=1

    for f in range(1,6):
        cf=get_collection(f"Equipment_F{f}", root)
        base=(f-1)*FLOOR_H
        # First Aid Kit near Stairwell A (front-left)
        first_aid(f, STAIR_A_X+2.0, -8.5, base, cf)
        # Emergency Go Bag near Stairwell B bottom corner (front-right)
        go_bag(f, STAIR_B_X+1.0, -9.0, base, cf)

        if f==1:
            # F1 exits: main exit front-center (y=-10), emergency exit rear (y=+10)
            fire_ext(f"F{f}_Main", 2.0, -9.4, base, cf)      # near main exit
            fire_ext(f"F{f}_Rear", 2.0, 9.4, base, cf)       # near rear emergency exit
            flashlight(f, 3.0, 9.2, base, cf)                # near rear exit (right side)
        else:
            # F2-5 exits: left near Stairwell A and right near Stairwell B, at rear (y=+10)
            fire_ext(f"F{f}_L", STAIR_A_X+1.0, 9.4, base, cf)
            fire_ext(f"F{f}_R", STAIR_B_X-1.0, 9.4, base, cf)
            flashlight(f, STAIR_B_X-2.0, 9.2, base, cf)      # near right emergency exit

    bpy.context.view_layer.update()
    return count

if __name__=="__main__":
    n=build_equipment()
    print("="*60)
    print(f"PHASE 3 COMPLETE - {n} equipment objects created (scene total {len(bpy.context.scene.objects)})")
    print("="*60)
