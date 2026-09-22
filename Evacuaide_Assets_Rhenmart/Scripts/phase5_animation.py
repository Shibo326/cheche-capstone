"""
EVACUAIDE - PHASE 5: Evacuation Path Camera Animation
=====================================================
Creates a smooth flythrough camera that walks the evacuation route on each
floor, from the top floor (5) down to Floor 1 and out the main exit.

  - 30 fps, 5 seconds per floor -> 150 frames per floor
  - 5 floors -> total 750 frames (frame 1..750)
  - Smooth Bezier interpolation on all keyframes
  - Camera stays at ~1.6 m eye height (VR standing) above each floor

The route per floor mirrors the blueprint evac paths:
  F5..F2: from far interior toward a stairwell, descending to next floor.
  F1: lobby toward the main exit and out to the plaza.

Also builds a single "EvacCam" and stores per-floor start frames so Phase 6
can bake per-floor animation FBX clips.

Units: meters. Blender 5.2.2, pure bpy.
"""
import bpy, math

FLOOR_H=3.0
FPS=30
SEC_PER_FLOOR=5
FR_PER_FLOOR=FPS*SEC_PER_FLOOR   # 150
EYE=1.6
STAIR_A_X=-12.0
STAIR_B_X= 12.0

def get_collection(name, parent=None):
    c=bpy.data.collections.get(name)
    if c is None:
        c=bpy.data.collections.new(name); (parent or bpy.context.scene.collection).children.link(c)
    return c

def floor_route(f):
    """Return a list of (x,y) waypoints for the walk on floor f (top->exit)."""
    if f==1:
        # lobby: from reception area -> center lobby -> main exit (front) -> out
        return [(-6,2),(-2,-1),(0,-5),(0,-9),(0,-13)]
    else:
        # office/exec: interior -> toward nearest stairwell -> rear exit landing
        # alternate which stairwell to add variety, both are valid routes
        if f in (5,3):
            sx=STAIR_A_X
            return [(-2,0),(-6,3),(sx+1.5,6),(sx,8.5),(sx,9.5)]
        else:
            sx=STAIR_B_X
            return [(2,0),(6,3),(sx-1.5,6),(sx,8.5),(sx,9.5)]

def build_animation():
    sc=bpy.context.scene
    sc.render.fps=FPS
    coll=get_collection("Evacuaide_Animation")

    # camera
    cam=bpy.data.objects.get("EvacCam")
    if cam is None:
        cd=bpy.data.cameras.new("EvacCam"); cam=bpy.data.objects.new("EvacCam",cd)
        coll.objects.link(cam)
    cam.data.lens=24
    cam.data.clip_start=0.05; cam.data.clip_end=500
    cam.animation_data_clear()

    # Build the full descending path: F5 -> F4 -> ... -> F1
    order=[5,4,3,2,1]
    frame=1
    per_floor_frames={}
    for oi,f in enumerate(order):
        base=(f-1)*FLOOR_H
        z=base+EYE
        pts=floor_route(f)
        per_floor_frames[f]=(frame, frame+FR_PER_FLOOR-1)
        n=len(pts)
        for i,(x,y) in enumerate(pts):
            fr=frame + round((FR_PER_FLOOR-1)*i/(n-1))
            cam.location=(x,y,z)
            # look direction: toward next waypoint (or forward)
            if i<n-1:
                nx,ny=pts[i+1]
                dirv=(nx-x,ny-y,0)
            else:
                dirv=(0,-1,-0.2)
            import mathutils
            d=mathutils.Vector(dirv)
            if d.length<1e-6: d=mathutils.Vector((0,-1,0))
            cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
            cam.keyframe_insert("location", frame=fr)
            cam.keyframe_insert("rotation_euler", frame=fr)
        frame+=FR_PER_FLOOR

    total_frames=frame-1
    sc.frame_start=1
    sc.frame_end=total_frames

    # smooth all fcurves -> bezier (handle both legacy + slotted Actions)
    def iter_fcurves(act):
        fcs = getattr(act, "fcurves", None)
        if fcs:
            for fc in fcs: yield fc
            return
        # Blender 4.4+/5.x slotted action
        for layer in getattr(act, "layers", []):
            for strip in getattr(layer, "strips", []):
                for slot in getattr(act, "slots", []):
                    cb = strip.channelbag(slot) if hasattr(strip, "channelbag") else None
                    if cb:
                        for fc in cb.fcurves: yield fc

    if cam.animation_data and cam.animation_data.action:
        for fc in iter_fcurves(cam.animation_data.action):
            for kp in fc.keyframe_points:
                kp.interpolation='BEZIER'
                kp.handle_left_type='AUTO_CLAMPED'
                kp.handle_right_type='AUTO_CLAMPED'
            fc.update()

    sc.camera=cam
    bpy.context.view_layer.update()
    return total_frames, per_floor_frames

if __name__=="__main__":
    tf,pf=build_animation()
    print("="*60)
    print(f"PHASE 5 COMPLETE - camera animation {tf} frames @ {FPS}fps")
    for f in sorted(pf): print(f"   Floor {f}: frames {pf[f][0]}..{pf[f][1]}")
    print("="*60)
