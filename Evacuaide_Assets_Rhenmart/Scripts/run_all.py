"""
EVACUAIDE - Master Runner
=========================
Rebuilds every EVACUAIDE asset from source in one headless Blender pass, then
exports Unity-ready building files and top-down floor maps.

Headless usage (from anywhere):
    blender --background --python run_all.py

Pipeline
--------
The building is DATA-DRIVEN: phase2_building.py reconstructs the full detailed
5-floor building (rooms, stairwells, elevators, windows, hazards, signage and
equipment) from building_layout.json - the single source of truth extracted
from the approved Blender scene. Because that one phase produces the entire
building, the older additive phases (phase3_hazards / phase4_signage /
phase4_equipment) are NOT re-run here; their content is already baked into the
layout JSON. They remain in the repo as the authoring tools that first created
that content and as standalone Unity FBX asset exporters.

Phases run here (each in a fresh scene):
    phase2_building.py    rebuild full building from JSON -> FBX per floor + full
    phase2b_facade.py     turn the plain shell into a color-banded glass tower
    phase2c_interior.py   furnish rooms per the blueprint program (the "loob")
    phase2d_detail.py     capstone detail polish (props, cars, lights, signage)
    phase2e_office.py     corporate office fit-out (cubicles, chairs, monitors)
    phase2f_finish.py     corporate material + floor/wall finish pass
    phase4b_exterior.py   corporate campus site (the "labas")
    phase9_export_glb.py  export Unity-ready GLB (+ FBX) of the full building
    phase8_floor_maps.py  render top-down floor-plan map PNGs (1..5)
    phase2e_cutaway.py    open the working scene into a dollhouse cross-section

phase2e runs LAST on purpose: the Unity/VR export (phase9) and floor maps
(phase8) need the complete closed building, so the cutaway - which only hides
ceilings + the front-facing shell - is applied afterwards, leaving the saved
working .blend readable floor-by-floor while the exported asset stays whole.

Note: phase2/2b/2c/4b MUST run in ONE Blender session (they mutate the same
scene), and the export/map phases read that same scene, so run_all keeps them
in the single process below rather than in fresh scenes per phase.

The SVG maps (phase5) and Unity project build are separate entrypoints:
    phase5_evac_maps.py   pure-python SVG maps (Blender's bundled python)
    build_unity.ps1       copy assets into the Unity project + build the APK
"""

import os
import runpy
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Standalone Unity FBX asset exporters (hazards/equipment as separate prefabs).
# Kept optional: enable if you want fresh individual asset FBXs for Unity.
ASSET_EXPORT_PHASES = [
    "phase3_hazards.py",
    "phase4_equipment.py",
]

# Core reproducible pipeline for the assembled building + Unity assets.
# Order matters: build the shell, decorate it (facade/interior/exterior), THEN
# export + render maps so the Unity asset and floor plans include everything.
PHASES = [
    "phase2_building.py",     # full building shell from building_layout.json
    "phase2b_facade.py",      # color-banded glass curtain-wall facade (labas)
    "phase2c_interior.py",    # room fit-out furniture per blueprint (loob)
    "phase2d_detail.py",      # capstone detail polish: props, cars, lights, signage
    "phase2e_office.py",      # corporate office fit-out: cubicles, chairs, monitors
    "phase2f_finish.py",      # corporate material + floor/wall finish pass
    "phase4b_exterior.py",    # corporate campus site (labas)
    "phase10_polish.py",      # minimal polish: exterior lamp posts + interior trims
    "phase9_export_glb.py",   # Unity-ready GLB + FBX of the decorated building
    "phase8_floor_maps.py",   # top-down floor-plan map renders
    "phase2e_cutaway.py",     # dollhouse cross-section for the working scene
]


def run(phase):
    path = os.path.join(SCRIPT_DIR, phase)
    if not os.path.exists(path):
        print("SKIP (missing):", phase)
        return
    print("\n" + "=" * 60)
    print("RUNNING:", phase)
    print("=" * 60)
    runpy.run_path(path, run_name="__main__")


def main():
    export_assets = "--with-asset-exports" in sys.argv
    if export_assets:
        for p in ASSET_EXPORT_PHASES:
            run(p)
    for p in PHASES:
        run(p)
    print("\nALL BLENDER PHASES COMPLETE")


if __name__ == "__main__":
    main()
