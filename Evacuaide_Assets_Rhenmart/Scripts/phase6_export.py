"""
EVACUAIDE - PHASE 6: FBX Export (Unity-ready)
==============================================
Applies transforms and exports the scene into the required folder tree:

Evacuaide_Assets_Rhenmart/
  Building/  OfficeBuilding_5F.fbx           (full shell + exterior)
  Floors/    Floor_01_Lobby.fbx .. Floor_05_Executive.fbx
  Hazards/   Bookshelf_Fall / CeilingTile_Crack / GlassPartition_Break /
             FilingCabinet_Topple / ElectricalPanel_Spark / DebrisPile .fbx
  Equipment/ Flashlight / EmergencyBag / FirstAidKit / FireExtinguisher .fbx
  Animations/EvacPath_Floor01.fbx .. EvacPath_Floor05.fbx  (camera clips)

Unity FBX settings (per spec):
  global_scale = 0.01
  bake_space_transform = True   (Apply Transform ON)
  axis_forward = '-Z', axis_up = 'Y'
  use_triangles = True

Blender 5.2.2, pure bpy.
"""
import bpy, os

try:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    ROOT = os.path.dirname(bpy.data.filepath) or os.getcwd()

FBX_COMMON = dict(
    use_selection=True,
    global_scale=0.01,
    apply_unit_scale=True,
    apply_scale_options='FBX_SCALE_NONE',
    bake_space_transform=True,      # Apply Transform ON
    use_mesh_modifiers=True,
    mesh_smooth_type='FACE',
    use_triangles=True,             # Triangulate ON
    axis_forward='-Z',
    axis_up='Y',
    path_mode='COPY',
    embed_textures=True,
    bake_anim=False,
    use_custom_props=False,
    check_existing=False,
)

def ensure_dir(p):
    os.makedirs(p, exist_ok=True); return p

def deselect_all():
    for o in bpy.context.scene.objects: o.select_set(False)

def select_names(names):
    deselect_all()
    n=0
    for nm in names:
        o=bpy.data.objects.get(nm)
        if o: o.select_set(True); n+=1
    if n:
        bpy.context.view_layer.objects.active = next(
            (bpy.data.objects.get(x) for x in names if bpy.data.objects.get(x)), None)
    return n

def select_pred(pred):
    deselect_all()
    active=None; n=0
    for o in bpy.context.scene.objects:
        if o.type=='MESH' and pred(o.name):
            o.select_set(True); active=o; n+=1
    if active: bpy.context.view_layer.objects.active=active
    return n

def apply_all_transforms():
    deselect_all()
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    for o in meshes: o.select_set(True)
    if meshes:
        bpy.context.view_layer.objects.active=meshes[0]
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    deselect_all()

def export_selection(filepath, **overrides):
    args=dict(FBX_COMMON); args.update(overrides)
    args["filepath"]=filepath
    bpy.ops.export_scene.fbx(**args)
    ok = os.path.exists(filepath)
    print(("  OK  " if ok else " FAIL "), os.path.relpath(filepath, ROOT),
          f"({os.path.getsize(filepath)} bytes)" if ok else "")
    return ok

def run():
    sc=bpy.context.scene
    # ensure everything visible (hidden objects are skipped by exporter)
    for o in sc.objects:
        o.hide_render=False; o.hide_viewport=False
        try: o.hide_set(False)
        except: pass

    # ---- APPLY TRANSFORMS (meshes only; camera excluded to keep anim) ----
    apply_all_transforms()

    dirs={k:ensure_dir(os.path.join(ROOT,k)) for k in
          ("Building","Floors","Hazards","Equipment","Animations")}
    written=[]

    # ---------- BUILDING (full structural shell + facade + exterior) ----------
    HAZ0=("Book","Elec","Glass","Debris","Ceil","File")
    def bld_ok(nm):
        if nm.startswith(("EXT_","FAC_")) or nm=="EVAC_AssemblyMarker":
            return True
        if nm.startswith(("F1_","F2_","F3_","F4_","F5_")):
            p=nm[:3]
            if any(nm.startswith(p+h) for h in HAZ0): return False
            if ("_ElevX" in nm) or ("ExitSign" in nm) or ("_Route" in nm): return False
            return True
        return False
    n=select_pred(bld_ok)
    if export_selection(os.path.join(dirs["Building"],"OfficeBuilding_5F.fbx")):
        written.append("Building/OfficeBuilding_5F.fbx")

    # ---------- FLOORS (structural per floor, no hazards/eq/signage) ----------
    floor_files={1:"Floor_01_Lobby",2:"Floor_02_Office",3:"Floor_03_Office",
                 4:"Floor_04_Office",5:"Floor_05_Executive"}
    # Floors = everything with the floor prefix, EXCLUDING hazards and signage
    # (those ship as their own dedicated FBX groups). Equipment uses EQ_ prefix
    # so it never matches a floor prefix.
    HAZ = ("Book","Elec","Glass","Debris","Ceil","File")   # hazard suffixes
    def is_hazard(nm, p):
        return any(nm.startswith(p+h) for h in HAZ)
    def is_signage(nm):
        return ("_ElevX" in nm) or ("ExitSign" in nm) or ("_Route" in nm) or ("_A" in nm and "Arrow" in nm)
    for f,fname in floor_files.items():
        pref=f"F{f}_"
        n=select_pred(lambda nm,p=pref: nm.startswith(p)
                      and not is_hazard(nm,p) and not is_signage(nm))
        if export_selection(os.path.join(dirs["Floors"],fname+".fbx")):
            written.append(f"Floors/{fname}.fbx")

    # ---------- HAZARDS (grouped by type, all floors) ----------
    hazard_groups={
        "Bookshelf_Fall":       lambda nm: "_Book" in nm,
        "CeilingTile_Crack":    lambda nm: "_Ceil" in nm,
        "GlassPartition_Break": lambda nm: "_Glass" in nm and nm.startswith(("F1_","F2_","F3_","F4_","F5_")),
        "FilingCabinet_Topple": lambda nm: "_File" in nm,
        "ElectricalPanel_Spark":lambda nm: "_Elec" in nm,
        "DebrisPile":           lambda nm: "_Debris" in nm,
    }
    for fname,pred in hazard_groups.items():
        n=select_pred(pred)
        if export_selection(os.path.join(dirs["Hazards"],fname+".fbx")):
            written.append(f"Hazards/{fname}.fbx")

    # ---------- EQUIPMENT (grouped by type, all floors) ----------
    equip_groups={
        "Flashlight":      lambda nm: nm.startswith("EQ_Flashlight"),
        "EmergencyBag":    lambda nm: nm.startswith("EQ_GoBag"),
        "FirstAidKit":     lambda nm: nm.startswith("EQ_FirstAid"),
        "FireExtinguisher":lambda nm: nm.startswith("EQ_FireExt"),
    }
    for fname,pred in equip_groups.items():
        n=select_pred(pred)
        if export_selection(os.path.join(dirs["Equipment"],fname+".fbx")):
            written.append(f"Equipment/{fname}.fbx")

    # ---------- ANIMATIONS (EvacCam per-floor clips) ----------
    cam=bpy.data.objects.get("EvacCam")
    per_floor={5:(1,150),4:(151,300),3:(301,450),2:(451,600),1:(601,750)}
    anim_files={1:"EvacPath_Floor01",2:"EvacPath_Floor02",3:"EvacPath_Floor03",
                4:"EvacPath_Floor04",5:"EvacPath_Floor05"}
    if cam:
        for f,fname in anim_files.items():
            s,e=per_floor[f]
            sc.frame_start=s; sc.frame_end=e
            deselect_all(); cam.select_set(True); bpy.context.view_layer.objects.active=cam
            ok=export_selection(os.path.join(dirs["Animations"],fname+".fbx"),
                                 object_types={'CAMERA'},
                                 bake_anim=True,
                                 bake_anim_use_all_actions=False,
                                 bake_anim_use_nla_strips=False)
            if ok: written.append(f"Animations/{fname}.fbx")
        sc.frame_start=1; sc.frame_end=750

    deselect_all()
    return written

if __name__=="__main__":
    files=run()
    print("="*60)
    print(f"PHASE 6 COMPLETE - {len(files)} FBX files exported")
    for f in files: print("   ", f)
    print("="*60)
