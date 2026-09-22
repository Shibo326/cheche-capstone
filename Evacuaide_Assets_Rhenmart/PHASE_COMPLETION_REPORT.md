# Evacuaide VR — Build Completion Report

VR-Based Earthquake Preparedness & Training Simulation
Blender 5.2.2 LTS → Unity / Meta Quest

Coordinate system: 1 Blender unit = 1 meter. Origin at building center.
X: -15..+15 (30 m wide), Y: -10 (front) ..+10 (rear), Z up.
Floor F base = (F-1) × 3 m. FBX export scale 0.01 → correct Unity meters.

Final scene: **660 objects**, saved as `Evacuaide_Complete_AllPhases.blend`.

---

## PHASE 1 — Building — COMPLETE (450 structural objects)

- 30 m × 20 m footprint, 3 m per floor, 15 m total (measured 30.3 × 20.3 × 15.4 m incl. wall/slab).
- Walls 0.3 m thick, doors 2.1 m, windows 1.2 m @ 0.9 m sill.
- Stairwell A (x=-12) + Stairwell B (x=+12), 3×6 m, same position all floors, stepped flights.
- Elevator bank: 2 shafts 2×2 m — center-top (F1), right (F2-4), center (F5).
- Per-floor color coding: F1 gray, F2 steel blue, F3 sage green, F4 warm yellow, F5 exec red.
- Rooms placed per blueprint: Security×2, Reception×2, Restrooms, Janitor×2 (F1);
  Conference, Restrooms, Manager Office, 12 workstations, Pantry, Storage (F2-4);
  Executive Office, Board Room, Exec Restroom, Pantry, Roof Access, Storage (F5).
- Emissive green exit doors (Main + rear on F1; left/right on F2-5).
- Collections: `Floor_01_Lobby` … `Floor_05_Executive` under `Evacuaide_Building`.

## PHASE 2 — Hazards — COMPLETE (60 objects, red emissive #FF2222)

- F1: falling bookshelf in both Security Offices, electrical panel near elevator,
  glass partition at Reception, debris zone above Main Lobby.
- F2-4: bookshelves near W1/W5/W10, electrical panel near Stairwell B, glass
  partition between Manager Office & Open Office, ceiling-tile debris above W6/W7,
  filing cabinet in Storage.
- F5: bookshelf in Executive Office, glass partition at Board Room wall, electrical
  panel near elevator, ceiling-tile debris above Board Room.
- Collection: `Evacuaide_Hazards` (Hazards_F1..F5).

## PHASE 3 — Emergency Equipment — COMPLETE (35 objects, emissive)

- First Aid Kit (white box + green cross #00FF00) near Stairwell A — all floors.
- Fire Extinguisher ×2 (red #FF3300) near each emergency exit — all floors.
- Emergency Go Bag (orange #FF8800) near Stairwell B corner — all floors.
- Flashlight (yellow #FFFF00) near right emergency exit — all floors.
- Collection: `Evacuaide_Equipment` (Equipment_F1..F5).

## PHASE 4 — Signage & Arrows — COMPLETE (84 objects)

- Green emissive floor arrows (#00FF44) every 2 m along evac routes, pointing to exits.
- Exit signs (green #00FF88) above each emergency exit @ 2.3 m.
- Elevator DO NOT USE red X (#FF0000) on every elevator door — rebuilt & verified.
- Assembly area green emissive circle marker at rear (y=18).
- Collection: `Evacuaide_Signage` (Signage_F1..F5).

## PHASE 4b — Exterior / Site Map — COMPLETE (28 objects)

- Green lawn ground plane, front plaza + walkway.
- Main entrance canopy over front door.
- Parking lot with 10 painted stalls (2 rows × 5).
- Assembly area concrete pad (rear) under the green marker.
- 4 trees at lot corners.
- Collection: `Evacuaide_Exterior`.

## PHASE 5 — Evacuation Camera Animation — COMPLETE (750 frames @ 30 fps)

- `EvacCam` flythrough, 5 s per floor, smooth Bezier interpolation.
- Descends F5 → F1 following evac routes to exits, ~1.6 m VR eye height.
- Frame ranges: F5 1-150, F4 151-300, F3 301-450, F2 451-600, F1 601-750.
- Collection: `Evacuaide_Animation`.

## PHASE 6 — FBX Export — COMPLETE (21 files)

Unity settings applied to every file: global_scale 0.01, Apply Transform ON
(bake_space_transform), axis forward -Z, up Y, triangulate ON, textures embedded.
All object transforms (loc/rot/scale) applied before export.

```
Evacuaide_Assets_Rhenmart/
├── Building/  OfficeBuilding_5F.fbx
├── Floors/    Floor_01_Lobby.fbx  Floor_02_Office.fbx  Floor_03_Office.fbx
│              Floor_04_Office.fbx  Floor_05_Executive.fbx
├── Hazards/   Bookshelf_Fall.fbx  CeilingTile_Crack.fbx  GlassPartition_Break.fbx
│              FilingCabinet_Topple.fbx  ElectricalPanel_Spark.fbx  DebrisPile.fbx
├── Equipment/ Flashlight.fbx  EmergencyBag.fbx  FirstAidKit.fbx  FireExtinguisher.fbx
└── Animations/EvacPath_Floor01.fbx .. EvacPath_Floor05.fbx
```

---

## Scripts (Scripts/)

- `phase1_building.py` — structural building generator
- `phase2_hazards.py` — hazard objects
- `phase3_equipment.py` — emergency equipment
- `phase4_signage.py` — arrows, exit/elevator signs, assembly marker
- `phase4b_exterior.py` — site/exterior environment
- `phase5_animation.py` — evacuation camera animation
- `phase6_export.py` — Unity FBX export

## QA renders (Renders/)

phase1_floor{1,2,5}_top, phase2_f{1,2}_top, phase3_f1 closeup, phase4_f2 arrows +
elevator-X closeup, phase4b_site, phase5_frame{375,680}, FINAL_complete.

## Notes / known limitations

- Building facade is a solid shell (thin glass window strips), so it reads as an
  opaque box from the exterior — correct for a VR interior-focused simulation.
- The flythrough path clips close to some walls at waypoints; usable as an evac
  preview. Tighten waypoints in `phase5_animation.py::floor_route` if a cleaner
  path is wanted.
- The scene previously contained stale objects from an earlier session (different
  scale/naming); these were removed so only the authoritative build remains.
