# EVACUAIDE — Building Solid QA Report
**Date:** 2026-09-22  
**File:** `Evacuaide_Building_Solid.blend`  
**Export:** `Building/OfficeBuilding_Assembled.glb` (553 KB, Y-up, EEVEE-ready)  
**Engine:** Blender 5.2 / BLENDER_EEVEE / 1600×1000

---

## Build Summary

| Item | Value |
|---|---|
| Footprint | 2000 × 1400 cm (20m × 14m) |
| Floor height | 350 cm (3.5m) each |
| Total height | 1750 cm (17.5m, 5 floors + roof) |
| Wall thickness | 20 cm |
| Slab thickness | 25 cm (shared floor/ceiling) |
| Total mesh objects | 84 |
| Materials | 33 |
| Lights | 3 (Key_Sun, Fill_Area, Rim_Area) |

---

## Collections

| Collection | Objects | Contents |
|---|---|---|
| Building | 7 | Struct_Columns, Struct_Slabs, Walls_F1–F5 |
| Furniture | 5 | Furn_F1–F5 (lobby, 3× office, exec) |
| Design | 11 | Glass facade, accent trims, windows E/W/N, lobby glass, canopy, roof, plinth |
| EvacMarkers | 28 | 3 arrows + stairpad + exit sign per floor + main exit + assembly |
| Equipment | 22 | 2× fire ext + first aid + flashlight per floor + 2× go bags |
| Hazards | 11 | Bookshelf F2–F5, electrical panel F2–F5, filing cabinet F2–F4 |

---

## Structural Fix (anti-lutang)

Previous issue: floors were separate trays with gaps — looked "floating".

Fix applied:
- **6 full-height columns** (0 → 1750 cm) tie all floors together vertically
- **6 shared slabs** at Z = 0, 350, 700, 1050, 1400, 1750 — each slab is simultaneously floor of upper floor + ceiling of lower floor
- **Walls span full floor height** (slab-to-slab, no gaps)
- **Stairwell shaft** runs continuously per floor with door gap on west wall

---

## Per-Floor Verification ✅

| Floor | Name | Color | Layout | Evac Route | Hazards |
|---|---|---|---|---|---|
| 1 | Lobby | 🟢 Green | Reception, security desk, 3× sofas, main exit door gap | Arrows → stairwell (right) + main exit (south) | — |
| 2 | Office | 🔵 Blue | 12 cubicles 4×3, conference room (glass walls), 4× filing cabinets | Arrows → blue stairwell pad → down | Bookshelf (N wall), electrical panel (E wall) |
| 3 | Office | 🟠 Orange | Same as F2 | Arrows → blue stairwell pad → down | Bookshelf, electrical panel |
| 4 | Office | 🟣 Purple | Same as F2 | Arrows → blue stairwell pad → down | Bookshelf, electrical panel, filing cabinet |
| 5 | Executive | 🔴 Red | Boardroom + 10 chairs, 2× exec desks, kitchenette | Arrows → blue stairwell pad → down | Bookshelf, electrical panel |

**All floors:** 3 green directional arrows per floor → blue stairwell pad → stairwell steps (visible) → pababa → ground main exit → yellow assembly area (south, -700 cm from building).

---

## Evacuation System

```
[Any floor office/exec area]
       ↓ green arrows
[Stairwell door (west wall gap)]
       ↓ steps
[Ground floor lobby]
       ↓ main exit door gap (south facade)
[Entrance canopy]
       ↓ EVAC_MainExitArrow
[EVAC_AssemblyPoint — yellow disc, 700cm south]
```

- Green arrows: `M_Exit` (emissive, 5.0 strength) — glow in VR
- Blue stairwell pads: `M_StairBlue` (emissive, 3.5 strength)
- Assembly point: `M_Assembly` (emissive yellow, 3.5 strength)
- All emissive materials visible in dark/post-earthquake VR environment

---

## Renders Produced

| File | Size | Description |
|---|---|---|
| `Renders/Hero_Building.png` | 1.7 MB | 3/4 perspective hero shot |
| `Renders/Elevation_Cutaway.png` | 735 KB | Front ortho elevation cutaway |
| `Renders/TopDown_FloorPlan.png` | 1.1 MB | Top-down plan view all 5 floors |

---

## Design Details Added

- Ribbon windows on **East, West, North** facades (4 panels per floor each side)
- **South facade**: full curtain-wall glass with vertical mullions (7 panels × 5 floors)
- **Ground lobby**: glass entrance sidelights flanking the main exit door
- **Entrance canopy** with 2 posts over main exit (south side)
- **Planters** flanking entrance
- **Accent trim stripe** per floor (color-coded: green/blue/orange/purple/red)
- **Ground plinth** (base slab) grounding the building
- **Sidewalk** leading to assembly area
- **Roof**: slab + 4-side parapet + stairwell access hut

---

## Asset Pipeline Status (original phases)

| Phase | Output | Status |
|---|---|---|
| Phase 2 | Building + 5 floor FBX | ✅ Done (QA 87/87 previously) |
| Phase 3 | 5 hazard FBX (pre/post) | ✅ Done |
| Phase 4 | 4 equipment FBX + GrabPoints | ✅ Done |
| Phase 5 | 5 SVG evac maps (bilingual) | ✅ Done |
| Phase 6 | 5 animation FBX (EvacArrow paths) | ✅ Done |
| **Assembled scene** | `Evacuaide_Building_Solid.blend` | ✅ **NEW — solid, no floating** |
| **Assembled export** | `OfficeBuilding_Assembled.glb` | ✅ **NEW — 553KB, Y-up, Unity ready** |

---

## Notes for Client

- All meshes are **placeholder/structural** — client provides final textured art assets
- Naming convention: `Shell_F{n}`, `Furn_F{n}`, `Walls_F{n}`, `EVAC_*`, `HZ_*`, `EQ_*`, `DSN_*`
- Export scale: Blender cm → Unity m (GLB Y-up, apply_modifiers=True)
- GrabPoints (XR Interaction Toolkit) already embedded in Equipment FBX files (Phase 4)
- Hazard pre/post states embedded in Hazards FBX files (Phase 3)
- Evacuation animation clips in Animations FBX files (Phase 6)
