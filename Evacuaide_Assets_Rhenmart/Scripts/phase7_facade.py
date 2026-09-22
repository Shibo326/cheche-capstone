"""
EVACUAIDE - PHASE 7: Building Facade / Exterior Polish
======================================================
Makes the tower read like a real corporate office building instead of a plain
gray box, WITHOUT touching the interior room layout or the export groupings.

Adds (into collection `Evacuaide_Facade`):
  - Precast concrete pilaster columns on the 4 corners + mid-spans
  - A glass curtain-wall band on ALL four sides of every floor, inset slightly,
    with horizontal spandrel + vertical mullion grid
  - Per-floor color accent band at each floor line (matches floor color coding)
  - Ground-floor double-height glazed entrance (front, over the main door)
  - Rooftop parapet + 3 HVAC units + roof-access penthouse + a simple sign band

Also retints the perimeter wall material to a cleaner precast tone.

Building footprint: X -15..15, Y -10..10. Floor F base = (F-1)*3. 5 floors.
Units: meters. Blender 5.2.2, pure bpy. Run anytime after phase1.
"""
import bpy, math

FOOT_X=30.0; FOOT_Y=20.0
HALF_X=15.0; HALF_Y=10.0
FLOOR_H=3.0; NFLOORS=5
TOTAL_H=FLOOR_H*NFLOORS

FLOOR_HEX={1:"#9AA0A6",2:"#4A90D9",3:"#5A8A5A",4:"#C8A830",5:"#8B2020"}

def _srgb(c): return c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4
def hexrgb(h):
    h=h.lstrip("#"); return tuple(_srgb(int(h[i:i+2],16)/255.0) for i in (0,2,4))

def mat_solid(name, hexstr, rough=0.6, metal=0.0):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes=True; b=m.node_tree.nodes.get("Principled BSDF"); rgb=hexrgb(hexstr)
    if b:
        b.inputs["Base Color"].default_value=(*rgb,1.0)
        b.inputs["Roughness"].default_value=rough
        b.inputs["Metallic"].default_value=metal
    return m

def mat_glass(name, hexstr="#3E5C6E", rough=0.08):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes=True; b=m.node_tree.nodes.get("Principled BSDF"); rgb=hexrgb(hexstr)
    if b:
        b.inputs["Base Color"].default_value=(*rgb,1.0)
        b.inputs["Roughness"].default_value=rough
        b.inputs["Metallic"].default_value=0.9   # reflective glazing look
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

def build_facade():
    coll=get_collection("Evacuaide_Facade")
    m_precast = mat_solid("Mat_Precast","#C9CBC8",0.7)
    m_pilaster= mat_solid("Mat_Pilaster","#AEB2B0",0.6)
    m_glass   = mat_glass("Mat_Facade_Glass")
    m_mullion = mat_solid("Mat_Mullion","#3A3E42",0.4,0.7)
    m_roof    = mat_solid("Mat_Roof","#5B5F63",0.8)
    m_hvac    = mat_solid("Mat_HVAC","#8A8E92",0.5,0.5)
    m_signband= mat_solid("Mat_SignBand","#1E2A38",0.4,0.2)

    # retint the interior/exterior perimeter wall material to clean precast
    mw=bpy.data.materials.get("Mat_Wall")
    if mw and mw.use_nodes:
        b=mw.node_tree.nodes.get("Principled BSDF")
        if b:
            b.inputs["Base Color"].default_value=(*hexrgb("#C9CBC8"),1.0)
            b.inputs["Roughness"].default_value=0.7

    n=0
    # Perimeter wall centre sits at +/-HALF, thickness 0.3 -> outer face at
    # +/-(HALF+0.15). Push facade elements just OUTSIDE that so they're visible.
    WALL_HALF_T=0.15
    out=0.10                       # how far the glass sits beyond the wall face
    band_h=0.45                    # spandrel/accent band height at each floor line
    win_h=FLOOR_H-band_h-0.15      # glazing height between bands

    # ---------- corner + midspan pilasters (full height) ----------
    pil_w=0.7
    xs=[-HALF_X, -HALF_X/2, 0.0, HALF_X/2, HALF_X]
    ys=[-HALF_Y, HALF_Y]
    for xi,x in enumerate(xs):
        for yi,y in enumerate(ys):
            box(f"FAC_Pil_X{xi}_Y{yi}", (pil_w,pil_w,TOTAL_H),
                (x, y+ (0.15 if y<0 else -0.15), TOTAL_H/2), m_pilaster, coll); n+=1
    # side pilasters on left/right walls
    for yi,y in enumerate([-HALF_Y/2,0,HALF_Y/2]):
        for x in (-HALF_X,HALF_X):
            box(f"FAC_PilSide_{'L' if x<0 else 'R'}_{yi}",(pil_w,pil_w,TOTAL_H),
                (x+(0.15 if x<0 else -0.15), y, TOTAL_H/2), m_pilaster, coll); n+=1

    # ---------- per-floor glass curtain wall + accent band on all 4 sides ----------
    for f in range(1,NFLOORS+1):
        base=(f-1)*FLOOR_H
        accent=mat_solid(f"Mat_Accent{f}", FLOOR_HEX[f], 0.5, 0.1)
        z_glass=base+0.2+win_h/2
        z_band =base+FLOOR_H-band_h/2
        # front (-Y) and rear (+Y) : outer face at yy +/- (WALL_HALF_T+out)
        for side,yy in (("F",-HALF_Y),("B",HALF_Y)):
            yface=yy-(WALL_HALF_T+out) if yy<0 else yy+(WALL_HALF_T+out)
            box(f"FAC_Glass_{side}{f}", (FOOT_X-2.0,0.06,win_h),(0,yface,z_glass),m_glass,coll); n+=1
            box(f"FAC_Band_{side}{f}", (FOOT_X-1.2,0.18,band_h),(0,yface,z_band),accent,coll); n+=1
            # vertical mullions every ~2.5 m
            cols=int((FOOT_X-2.0)//2.5)
            for i in range(cols+1):
                mx=-((FOOT_X-2.0)/2)+i*((FOOT_X-2.0)/cols)
                box(f"FAC_Mul_{side}{f}_{i}", (0.10,0.12,win_h),(mx,yface,z_glass),m_mullion,coll); n+=1
        # left (-X) and right (+X) : outer face at xx +/- (WALL_HALF_T+out)
        for side,xx in (("L",-HALF_X),("R",HALF_X)):
            xface=xx-(WALL_HALF_T+out) if xx<0 else xx+(WALL_HALF_T+out)
            box(f"FAC_Glass_{side}{f}", (0.06,FOOT_Y-2.0,win_h),(xface,0,z_glass),m_glass,coll); n+=1
            box(f"FAC_Band_{side}{f}", (0.18,FOOT_Y-1.2,band_h),(xface,0,z_band),accent,coll); n+=1
            rows=int((FOOT_Y-2.0)//2.5)
            for i in range(rows+1):
                my=-((FOOT_Y-2.0)/2)+i*((FOOT_Y-2.0)/rows)
                box(f"FAC_Mul_{side}{f}_{i}", (0.12,0.10,win_h),(xface,my,z_glass),m_mullion,coll); n+=1

    # ---------- ground-floor double-height glazed entrance (front center) ----------
    ent_w=8.0; ent_h=5.4; ey=-HALF_Y-(WALL_HALF_T+out)
    box("FAC_Entrance_Glass",(ent_w,0.06,ent_h),(0,ey,ent_h/2),m_glass,coll); n+=1
    box("FAC_Entrance_FrameT",(ent_w+0.3,0.16,0.35),(0,ey,ent_h),m_mullion,coll); n+=1
    for sx in (-ent_w/2,0,ent_w/2):
        box(f"FAC_Entrance_MulV_{sx:.0f}",(0.14,0.16,ent_h),(sx,ey,ent_h/2),m_mullion,coll); n+=1

    # ---------- rooftop parapet + HVAC + penthouse + sign band ----------
    rz=TOTAL_H
    # parapet ring (4 low walls)
    par_h=0.9; pt=0.25
    box("FAC_Parapet_F",(FOOT_X,pt,par_h),(0,-HALF_Y,rz+par_h/2),m_precast,coll); n+=1
    box("FAC_Parapet_B",(FOOT_X,pt,par_h),(0, HALF_Y,rz+par_h/2),m_precast,coll); n+=1
    box("FAC_Parapet_L",(pt,FOOT_Y,par_h),(-HALF_X,0,rz+par_h/2),m_precast,coll); n+=1
    box("FAC_Parapet_R",(pt,FOOT_Y,par_h),( HALF_X,0,rz+par_h/2),m_precast,coll); n+=1
    # roof deck
    box("FAC_RoofDeck",(FOOT_X-0.6,FOOT_Y-0.6,0.1),(0,0,rz+0.05),m_roof,coll); n+=1
    # HVAC units
    for i,(hx,hy) in enumerate([(-6,3),(0,-3),(6,4)]):
        box(f"FAC_HVAC_{i}",(2.2,1.6,1.1),(hx,hy,rz+0.65),m_hvac,coll); n+=1
    # roof-access penthouse (matches interior RoofAccess on right)
    box("FAC_Penthouse",(3.2,3.2,2.6),(11,7,rz+1.3),m_precast,coll); n+=1
    box("FAC_Penthouse_Door",(0.9,0.06,2.1),(11,7-1.6,rz+1.05),m_mullion,coll); n+=1
    # front sign band on the parapet ("EVACUAIDE TOWER" plate)
    box("FAC_SignBand",(10,0.22,1.0),(0,-HALF_Y-(WALL_HALF_T+out+0.05),rz+0.6),m_signband,coll); n+=1

    bpy.context.view_layer.update()
    return n

if __name__=="__main__":
    n=build_facade()
    print("="*60)
    print(f"PHASE 7 FACADE COMPLETE - {n} facade/roof objects (scene total {len(bpy.context.scene.objects)})")
    print("="*60)
