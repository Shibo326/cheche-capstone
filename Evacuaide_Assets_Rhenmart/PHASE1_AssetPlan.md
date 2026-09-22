# EVACUAIDE — Phase 1: Asset Planning & Specifications

**Project:** Evacuaide — Unity VR Earthquake Simulation (Meta Quest)
**Environment:** 5-Floor Philippine Office Building
**Target:** Low-poly, FBX export, scale 0.01 (Blender cm → Unity m)
**Author role:** 3D Environment Architect

---

## Global Conventions

| Item | Value |
|---|---|
| Unit scale in Blender | 1 Blender unit = 1 cm (export at scale 0.01 → 1 m in Unity) |
| Floor height | 350 cm (3.5 m) per floor |
| Building footprint | 2000 cm × 1400 cm (20 m × 14 m) |
| Poly budget (building) | ~15k tris total, ~3k per floor |
| Poly budget (props) | 200–800 tris each |
| Origin | Building origin at ground-floor center, Z=0 at floor 1 |
| Naming | `PascalCase_WithUnderscores`, Unity-safe (no spaces) |

### Floor Color Code (for review + material IDs)

| Floor | Name | Color (hex) | Purpose |
|---|---|---|---|
| 1 | Lobby / Ground | `#4CAF50` green | Entry, reception, main + emergency exits |
| 2 | Office | `#2196F3` blue | Open office |
| 3 | Office | `#FF9800` orange | Open office |
| 4 | Office | `#9C27B0` purple | Open office |
| 5 | Executive | `#F44336` red | Executive, pantry, roof access |

---

## Floor-by-Floor Asset List

### Floor 1 — Lobby / Ground (green)
**Rooms:** Main lobby, reception desk area, security desk, main entrance vestibule, emergency exit corridor, elevator lobby, stairwell (enclosed), ground restrooms.

- Furniture: reception counter, waiting sofas (×3), coffee table, security desk, potted plants (×4), wall directory board.
- Emergency equipment: fire extinguisher (×2), first aid kit (wall), emergency go bag (security desk), flashlight (security desk), fire alarm pull station.
- Route markers: green EXIT signs above main + emergency doors, floor arrows toward assembly area, blue stairwell marker.
- Hazards: glass partition (facade), ceiling tiles (lobby), reception glass panel.

### Floors 2–4 — Open Office (blue / orange / purple)
**Rooms:** Open cubicle bullpen (12 cubicles), 1 conference room, pantry corner, male + female restrooms, stairwell (enclosed), 2 emergency exits, server/utility closet.

- Furniture: cubicle desks + partitions (×12), office chairs (×12), conference table + 8 chairs, whiteboard, filing cabinets (×4), bookshelves (×3), water dispenser, printer station.
- Emergency equipment: fire extinguisher (×2 per floor), first aid kit (wall near stairwell), flashlight (near each exit).
- Route markers: green exit arrows to nearest stairwell, blue stairwell indicators, red hazard-zone markers near glass/shelving.
- Hazards: falling bookshelf, cracked ceiling tile, broken glass partition (conference room), toppled filing cabinet, sparking electrical panel (utility closet).

### Floor 5 — Executive (red)
**Rooms:** Executive office (×2), boardroom, executive pantry/kitchenette, reception/PA desk, restrooms, stairwell, roof access door + stairs.

- Furniture: executive desks (×2), leather chairs, boardroom table + 10 chairs, lounge sofa set, bookshelves (×2), kitchenette counter + cabinets, mini fridge.
- Emergency equipment: fire extinguisher (×2), first aid kit, go bag (PA desk), flashlight, roof-access emergency light.
- Route markers: exit arrows to stairwell, roof-access marker, blue stairwell indicator.
- Hazards: falling bookshelf, ceiling tiles (boardroom), glass partition (executive office), electrical panel (pantry).

---

## Hazard Placement Guide (per floor)

| Hazard | Floor(s) | Location | Pre-state | Post-state |
|---|---|---|---|---|
| Falling bookshelf | 2,3,4,5 | Against wall near cubicles/office | Upright, books shelved | Toppled forward, books scattered |
| Cracked ceiling tile | 1,2,3,4,5 | Corridor / open ceiling grid | Flat tile in grid | Cracked, hanging/dropped |
| Broken glass partition | 1,2,3,4,5 | Conference / executive glass wall | Clear intact pane | Shattered with crack lines + shards |
| Toppled filing cabinet | 2,3,4 | Beside cubicles | Upright, drawers closed | Fallen on side, drawers open |
| Sparking electrical panel | 2,3,4,5 | Utility/server closet | Closed panel, door shut | Door ajar, exposed wires + spark emitter point |

---

## Emergency Equipment List (interactable, VR grab scale)

| Object | Real size (approx) | Blender size (cm) | Notes |
|---|---|---|---|
| Flashlight | 20 cm long | 20 | Cylinder body, lens front, grip texture. Add spotlight anchor at lens. |
| Emergency go bag | 45 cm tall backpack | 45 | Boxy backpack, straps, red cross patch. |
| First aid kit | 25 cm box | 25 | White box, red cross, handle + latch. |
| Fire extinguisher | 50 cm tall | 50 | Red cylinder, nozzle, gauge, pin. |

All equipment gets an empty "GrabPoint" at the natural grip location for Unity XR Interaction Toolkit socket alignment.

---

## Evacuation Route Marker System

- **Green arrows** — direction of travel to nearest exit/stairwell.
- **Blue markers** — stairwell entrances.
- **Red markers** — hazard zones (avoid).
- **Yellow markers** — outdoor assembly area (ground level only).
- **Path lines** — continuous glowing route from each room → stairwell → ground exit.
