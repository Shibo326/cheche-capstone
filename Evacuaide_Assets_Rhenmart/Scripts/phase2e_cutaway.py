"""
EVACUAIDE - Phase 2e: Dollhouse Cutaway
=======================================
Turns the fully assembled, facade-wrapped tower into a readable "dollhouse"
cross-section so every floor's evacuation layout is visible at a glance, and
defensively removes any stray oversized/off-site junk objects left by older
authoring passes.

Runs in the SAME Blender session as phase2/2b/2c/2d/4b, after the building and
its facade exist. It only hides objects (never deletes structural geometry), so
the cutaway is fully reversible by clearing hide flags.

What it does
------------
1. Purge junk: mesh objects that sit far outside the building envelope or are
   absurdly oversized (relics of a centimetre/metre scale bug). This is a
   safety net - a clean pipeline produces none.
2. Open the dollhouse front:
     - hide every floor ceiling (F*_Ceiling)
     - hide the front interior walls (F*_Wall_F) and any front windows
     - hide the front-facing facade layer (FAC_*_F* glass/mullions/bands,
       entrance, front parapet/sign) and the entrance canopy
   The back + side facade, roof, penthouse and landscaped grounds stay for
   context.

Headless usage (standalone, on an already-built .blend):
    blender your.blend --background --python phase2e_cutaway.py
"""

import bpy


# The building + its landscaped campus is comfortably inside a 60m radius and
# nothing legitimate is taller than the ~16m tower or wider than ~9m (site
# lawn/lot are flat pads). The scale-bug relics were unmistakable: coordinates
# in the hundreds/thousands (a cm value read as metres -> x=778, z=1436) and/or
# single-mesh spans of 60-190m. We flag ONLY those extremes so real site props
# (trees at x=+/-44, cars at y=-31, flag poles) are never touched.
FAR_COORD = 60.0     # metres from origin; grounds stay well within this
HUGE_DIM = 50.0      # metres; no legit solid part is this large (flat pads excl.)


def _is_junk(o):
    """True only for unmistakable scale-bug relics: flung far off-site or a
    single mesh larger than the whole tower. Deliberately conservative - it is
    a safety net, not a general cleaner, and must never remove real geometry.
    """
    if o.type != "MESH":
        return False
    lx, ly, lz = o.location
    dx, dy, dz = o.dimensions
    far_off = (
        abs(lx) > FAR_COORD
        or abs(ly) > FAR_COORD
        or abs(lz) > FAR_COORD
    )
    # A huge *solid* volume (all three dims large) is a relic; flat site pads
    # (lawn, parking lot, walkways) are wide but paper-thin, so exclude those.
    huge_solid = dx > HUGE_DIM and dy > HUGE_DIM and dz > 3.0
    huge_any = (dx > 100.0 or dy > 100.0 or dz > HUGE_DIM)
    return far_off or huge_solid or huge_any


def purge_junk():
    junk = [o for o in bpy.data.objects if _is_junk(o)]
    names = [o.name for o in junk]
    for o in junk:
        bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.meshes):
        if m.users == 0:
            bpy.data.meshes.remove(m)
    print(f"[cutaway] purged {len(names)} junk object(s)")
    return names


def _hide(o):
    o.hide_set(True)
    o.hide_viewport = True
    o.hide_render = True


def open_dollhouse():
    """Hide ceilings + the whole front-facing shell so floors are visible."""
    hidden = 0
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        n = o.name

        # Interior: every floor ceiling, the front interior wall, front windows.
        interior_front = (
            n.endswith("_Ceiling")
            or n.endswith("_Wall_F")
            or n.endswith("_Win_F")
        )

        # Exterior facade front layer (front plane is y = -10):
        # glass panels, vertical mullions, spandrel bands, the glazed entrance,
        # the front parapet cap and the sign band, plus the entrance canopy.
        facade_front = (
            n.startswith("FAC_Glass_F")
            or n.startswith("FAC_Mul_F")
            or n.startswith("FAC_Band_F")
            or n.startswith("FAC_Entrance_")
            or n == "FAC_SignBand"
            or n == "FAC_Parapet_F"
            or n in ("EXT_CanopyGlass", "EXT_CanopyRoof")
        )

        if interior_front or facade_front:
            _hide(o)
            hidden += 1
    print(f"[cutaway] hid {hidden} front/ceiling object(s) for dollhouse view")
    return hidden


def main():
    print("=" * 60)
    print("PHASE 2e: DOLLHOUSE CUTAWAY")
    print("=" * 60)
    purge_junk()
    open_dollhouse()
    # Persist if we're editing a saved file directly (headless standalone run).
    if bpy.data.filepath:
        bpy.ops.wm.save_mainfile()
        print("[cutaway] saved", bpy.data.filepath)
    print("PHASE 2e COMPLETE")


if __name__ == "__main__":
    main()
