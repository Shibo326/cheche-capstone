# EVACUAIDE — Unity Migration Guide (Plug-and-Play)

This guide gets the 3D building + evacuation maps into the Unity VR project and
into a playable scene. Everything is already exported and copied; you mostly
click one menu item.

Target: **Unity 2022.3 LTS / Unity 6 LTS**, OpenXR + XR Interaction Toolkit,
Meta Quest 2 / 3 / 3S (Android build).

---

## 0. TL;DR (fastest path)

1. Open the `EvacuaideVR` project in Unity.
2. Top menu: **Evacuaide → Import & Build Scene**.
3. Press **Play** (or File → Build to deploy to Quest).

That's it. The building spawns at the origin, an XR rig is placed in the
lobby, and grabbable equipment is laid out. The rest of this doc explains what
happened and how to adjust it.

---

## 1. What's already in the project

All assets are copied into `EvacuaideVR/Assets/Evacuaide/`:

| Folder | Files | What it is |
|---|---|---|
| `Building/` | `OfficeBuilding_5F.fbx`, `OfficeBuilding_5F.glb` | The full assembled 5-floor tower (walls, floors, stairs, elevators, facade, furniture, evac signage, equipment + hazards baked in) |
| `Floors/` | `Floor_01..05.fbx` | Each floor exported separately (for per-floor loading if you want it) |
| `Equipment/` | `Flashlight, EmergencyBag, FirstAidKit, FireExtinguisher .fbx` | **Grabbable** props as standalone objects |
| `Hazards/` | 5 hazard `.fbx` | Standalone animated/interactive hazards |
| `EvacuationMaps/` | `EvacMap_Floor01..05.svg` + `Floor_01..05_Map.png` | 2D floor plans (SVG for vector UI, PNG as ready-to-use textures) |
| `Animations/` | `EvacPath_Floor01..05.fbx` | Evacuation-route camera fly-throughs per floor |

---

## 2. Which building file to use — FBX vs GLB

Both files contain the **exact same geometry** (1,910 meshes, 85 materials,
emissive evac signage preserved in both). We verified this by re-importing each.

- **`OfficeBuilding_5F.fbx`** — this is what the auto-importer wires into the
  scene. Unity's FBX importer gives you automatic collider generation and
  clean material slots. **Use this as the main building** (default).
- **`OfficeBuilding_5F.glb`** — keep as a backup / reference. GLB carries the
  PBR + emissive values very cleanly; import it only if a material looks off in
  the FBX and you want to compare.

You do **not** need both in the scene. Pick the FBX (default) unless you have a
reason to switch.

---

## 3. Import settings (auto-applied, here for reference)

The menu item **Evacuaide → 1. Configure FBX Import Settings** sets, on every
model under `Assets/Evacuaide/`:

- **Scale:** `useFileScale = true`, `globalScale = 1` → **1 Unity unit = 1 metre**.
  The building is ~30 m × 20 m footprint, 5 floors × 3 m = 15 m tall. A 1.6 m
  camera is human eye height. No manual rescaling needed.
- **Read/Write enabled** (needed for runtime collider/mesh work).
- **Normals: Import** (keeps the authored shading).
- **Colliders:** auto-added on `Building/` and `Hazards/` (so the player can't
  walk through walls). Equipment gets colliders when made grabbable.
- **Materials:** `ImportStandard` — Unity builds standard materials from the
  embedded ones. Emissive materials (exit signs, evac arrows, hazard glow,
  first-aid green, go-bag orange) come in as emissive.

If you re-copy fresh assets later, just re-run this menu item.

---

## 4. Orientation & placement facts

- **Up axis:** Y-up (Unity native). Exported with Y-up for GLB and
  `-Z forward / Y up` for FBX, so the tower stands upright with no rotation.
- **Origin:** building centre is at world `(0,0,0)`; floor 1 slab top is ~`y=0`.
  Floor N ground is at `y = (N-1) * 3`.
- **Front of building** faces **-Z** (the main entrance, plaza, canopy and
  parking are on the -Z side). Rear (+Z) has the emergency exit and the green
  **assembly / muster point** ring.
- **Player spawn:** the rig is placed at about `(0, 0, -6)` in the lobby,
  facing into the building. Move `PlayerRig` / `XR Origin` to change it.

---

## 5. IMPORTANT: equipment & hazards are baked in

The assembled building **already contains visual copies** of the emergency
equipment (fire extinguishers, first-aid kits, go-bags, flashlights) and the
hazards (bookshelf, glass partition, electrical panel, ceiling debris) placed
per floor per the blueprint.

The standalone `Equipment/*.fbx` and `Hazards/*.fbx` are the **interactive**
versions — these are the ones you make grabbable / animate. So:

- The building's baked-in equipment/hazards are **visual placeholders** that
  show correct positions.
- For gameplay, place the **standalone** grabbable Equipment and animated
  Hazard prefabs at those same spots (the importer drops a starter set near the
  lobby; reposition per floor as your design needs).
- If you don't want the visual duplicates, you can hide the baked-in
  `EQ_*` / hazard objects inside the building prefab — but they're low-cost and
  usually fine to leave as background dressing.

---

## 6. Using the evacuation maps

- **PNG** (`Floor_0N_Map.png`, 1600×1100) — drop straight onto a quad / world-
  space UI `RawImage` as a "You-Are-Here" board. No extra package needed.
- **SVG** (`EvacMap_Floor0N.svg`) — crisp at any size but needs the Unity
  **Vector Graphics** package (`com.unity.vectorgraphics`). Use PNG if you want
  zero setup.

Each map is colour-coded per floor (grey F1 / blue F2 / green F3 / gold F4 /
maroon F5) matching the coloured accent band on that floor of the 3D tower, so
players can cross-reference the map with the building.

---

## 7. Performance (Quest budget)

- **Total geometry: ~31,700 triangles** for the entire 5-floor building + site.
  That is very light for a standalone Quest 2/3 (which handles hundreds of
  thousands). You have huge headroom for characters, NPCs, and effects.
- 85 materials, mostly simple. Consider a texture atlas / material merge only
  if you add many more props later.
- Everything is hard-surface boxes/cylinders — no heavy subdivision.

---

## 8. Rebuilding the assets from source (optional)

If the design changes, regenerate everything in one command (needs Blender 5.2
at the path in `build_all.ps1`):

```
blender --background --python Scripts\run_all.py
```

Then re-copy `Building/OfficeBuilding_5F.*` and `Renders/FloorMaps/*.png` into
the Unity folders (or run `build_all.ps1` which copies for you), and re-run
**Evacuaide → 1. Configure FBX Import Settings** in Unity.

---

## 9. If something looks wrong

| Symptom | Fix |
|---|---|
| Building is tiny / giant | Re-run **Configure FBX Import Settings** (enforces 1 unit = 1 m). |
| Can walk through walls | Confirm colliders were added (Building importer `addCollider`). Re-run the menu. |
| Exit signs / arrows not glowing | Material emission got dropped — reimport the **GLB** version, or set the material's Emission in Unity. |
| Player spawns outside | Move `PlayerRig` / `XR Origin` to `(0,0,-6)` (lobby). |
| No VR controls | Install **XR Interaction Toolkit** via Package Manager, then re-run Import & Build Scene. |
