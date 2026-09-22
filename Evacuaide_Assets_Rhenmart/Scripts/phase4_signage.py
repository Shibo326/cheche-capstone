"""
EVACUAIDE - PHASE 4: Evacuation Arrows, Exit Signs, Elevator Signs, Assembly
============================================================================
Adds:
  - Green emissive floor arrows every 2 m along evacuation routes, pointing
    toward nearest exit. On floor (Z = base + 0.05). Scale 0.5 x 0.3.
  - Exit signs (green emissive panel) above each Emergency Exit door,
    0.6 x 0.2, mounted at 2.3 m. Face text plate "EXIT / LABASAN".
  - Elevator DO NOT USE red X panel on each elevator door.
  - Assembly area marker: green emissive circle on the ground (rear/outside).

Materials:
  arrows  green #00FF44 emit 2.0
  exits   green #00FF88 emit 3.0
  elevator red  #FF0000 emit 2.5
Units: meters. Blender 5.2.2, pure bpy. Run after phase3.
"""
import bpy, math

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

def link_only(ob, coll):
    for c in list(ob.users_collection): c.objects.unlink(ob)
    coll.objects.link(ob)

def box(name, size, loc, mat, coll):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    ob=bpy.context.active_object; ob.name=name; ob.scale=size
    if mat: ob.data.materials.append(mat)
    link_only(ob, coll); return ob

def arrow_mesh(name, loc, angle_z, mat, coll, length=0.5, width=0.3):
    """Flat chevron arrow lying on the floor, pointing +X then rotated by angle_z."""
    import bmesh
    hl=length/2.0; hw=width/2.0
    verts=[(-hl,-hw,0),(-hl,hw,0),(0.0,hw,0),(hl,0.0,0),(0.0,-hw,0)]
    faces=[(0,1,2,4),(2,3,4)]
    me=bpy.data.meshes.new(name)
    me.from_pydata([ (x,y,z) for (x,y,z) in verts ], [], faces)
    me.update()
    ob=bpy.data.objects.new(name, me)
    ob.location=loc; ob.rotation_euler=(0,0,angle_z)
    if mat: ob.data.materials.append(mat)
    coll.objects.link(ob)
    return ob

def exit_sign(name, loc, mat, coll, w=0.6, h=0.2):
    return box(name, (w,0.05,h), loc, mat, coll)

def elevator_x(name, loc, mat, coll, size=1.4):
    """Two crossed diagonal bars forming a big red X on the elevator door face.
    Door faces -Y, so the X lies in the X-Z plane. Bars are long (size) in
    their local X, thin in Z, very thin in Y, rotated +/-45 deg about Y."""
    bar=(size, 0.04, 0.14)     # long, paper-thin in Y, tall enough to read
    b1=box(name+"_a", bar, loc, mat, coll)
    b1.rotation_euler=(0, math.radians(45), 0)
    b2=box(name+"_b", bar, loc, mat, coll)
    b2.rotation_euler=(0, math.radians(-45), 0)
    return [b1,b2]

def route_arrows(prefix, pts, base, angle_from_dir, mat, coll):
    """Place arrows every 2 m along a polyline pts=[(x,y),...] toward last pt."""
    count=0
    for i in range(len(pts)-1):
        x0,y0=pts[i]; x1,y1=pts[i+1]
        seg=math.hypot(x1-x0,y1-y0)
        if seg<1e-6: continue
        n=max(1,int(seg//2.0))
        ang=math.atan2(y1-y0, x1-x0)
        for k in range(n):
            t=(k+0.5)/n
            x=x0+(x1-x0)*t; y=y0+(y1-y0)*t
            arrow_mesh(f"{prefix}_A{count}", (x,y,base+0.05), ang, mat, coll)
            count+=1
    return count

def build_signage():
    m_arrow=mat_emissive("Mat_Arrow","#00FF44",2.0)
    m_exit =mat_emissive("Mat_ExitSign","#00FF88",3.0)
    m_elev =mat_emissive("Mat_ElevX","#FF0000",2.5)
    m_sign_txt=mat_emissive("Mat_SignText","#FFFFFF",1.0)

    root=get_collection("Evacuaide_Signage")
    total=0

    # elevator positions per floor (from phase1/2): F1 center-top y6.5,
    # F2-4 right side (11,0.5), F5 center y5.5
    elev_centers={1:(0.0,6.5),2:(11.0,0.5),3:(11.0,0.5),4:(11.0,0.5),5:(0.0,5.5)}

    for f in range(1,6):
        cf=get_collection(f"Signage_F{f}", root)
        base=(f-1)*FLOOR_H

        # -------- evacuation route arrows --------
        if f==1:
            # Security/Reception -> Main Lobby -> Main Exit (front-center y-10)
            pts=[(-11,-6),(-6,-3),(-2,-6),(0,-9.4)]
            total+=route_arrows(f"F{f}_RouteMain", pts, base, None, m_arrow, cf)
            # Secondary -> rear emergency exit
            pts2=[(-2,0),(0,4),(0,9.0)]
            total+=route_arrows(f"F{f}_RouteRear", pts2, base, None, m_arrow, cf)
        else:
            # workstations -> nearest stairwell -> rear emergency exit
            # left route toward Stairwell A rear exit
            ptsL=[(-4,0),(-8,3),(STAIR_A_X,7),(STAIR_A_X,9.0)]
            total+=route_arrows(f"F{f}_RouteL", ptsL, base, None, m_arrow, cf)
            # right route toward Stairwell B rear exit
            ptsR=[(3,0),(7,3),(STAIR_B_X,7),(STAIR_B_X,9.0)]
            total+=route_arrows(f"F{f}_RouteR", ptsR, base, None, m_arrow, cf)

        # -------- exit signs above emergency exit doors --------
        if f==1:
            exit_sign(f"F{f}_ExitSign_Main", (0.0,-9.9,base+2.3), m_exit, cf)
            exit_sign(f"F{f}_ExitSign_Rear", (0.0, 9.9,base+2.3), m_exit, cf)
            total+=2
        else:
            exit_sign(f"F{f}_ExitSign_L", (STAIR_A_X, 9.9, base+2.3), m_exit, cf)
            exit_sign(f"F{f}_ExitSign_R", (STAIR_B_X, 9.9, base+2.3), m_exit, cf)
            total+=2

        # -------- elevator DO NOT USE red X on each door --------
        cx,cy=elev_centers[f]
        gap=0.15
        for i,dx in enumerate([-(1.0+gap/2.0),(1.0+gap/2.0)],1):
            ex=cx+dx
            elevator_x(f"F{f}_ElevX{i}", (ex, cy-1.03, base+1.2), m_elev, cf)
            total+=2

    # -------- Assembly area marker (rear/outside, ground level) --------
    ca=get_collection("Signage_Assembly", root)
    bpy.ops.mesh.primitive_cylinder_add(radius=3.0, depth=0.05,
        location=(0,18.0,0.03), vertices=32)
    ob=bpy.context.active_object; ob.name="EVAC_AssemblyMarker"
    ob.data.materials.append(m_exit); link_only(ob, ca)
    # inner ring hole look: smaller dark disc omitted; keep simple ring via scale
    total+=1

    bpy.context.view_layer.update()
    return total

if __name__=="__main__":
    n=build_signage()
    print("="*60)
    print(f"PHASE 4 COMPLETE - {n} signage/arrow objects created (scene total {len(bpy.context.scene.objects)})")
    print("="*60)
