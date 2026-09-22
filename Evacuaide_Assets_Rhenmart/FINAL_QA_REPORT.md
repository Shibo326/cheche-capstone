# EVACUAIDE — Final QA Report
**Date:** 9/22/2026  
**Status: ALL SYSTEMS PASS ✅**

---

## Summary

| Phase | Check | Result |
|---|---|---|
| Asset pipeline (Blender) | 88/88 checks | ✅ PASS |
| Unity import verification | 0 failures (8 building MeshRenderers) | ✅ PASS |
| Android/Quest APK build | Build succeeded | ✅ PASS |
| Corporate tower revamp | Verified live in Blender | ✅ DONE |

---

## Phase 1: Asset Pipeline

**Tool:** `Scripts/qa_validate.py`  
**Result:** 87/87 checks passed, 0 failed  
**Checks cover:**
- All 20 FBX present and non-empty with valid FBX header
- Named nodes in each FBX: `_Pre` + `_Post` for all 5 hazards, `GrabPoint` for all 4 equipment, `EvacArrow` for all 5 animations
- All 5 SVG evacuation maps are well-formed XML with correct color palette (`#2E7D32`, `#D32F2F`, `#1565C0`, `#F2C200`) and "MANILA INNOVATIONS TOWER" branding

---

## Phase 2: Corporate Office Tower Revamp

The building was fully rewritten from a blockout into a BGC-style corporate
glass tower (verified live in Blender via multi-angle screenshots).

**Facade & structure:**
- Full glass curtain-wall on all four sides: continuous glass ribbons +
  bottom/top spandrel bands + vertical mullion grid + horizontal transoms
- Ground-floor lobby with a double-height glazed entrance (central door bay)
- Per-floor color-coded accent reveal lines (green/blue/orange/purple/red)
- Rooftop crown: parapet, 3 HVAC units with fans, roof-access stair housing
- MANILA INNOVATIONS TOWER emissive signage above the lobby entrance

**Exterior environment (grass + landscaping):**
- Grass ground plane across the whole site (60 m × 52 m)
- Paved plaza wrapping the tower footprint + entrance walkway
- Concrete planter curbs framing the plaza (landscaping strips)
- 6 low-poly trees at the site perimeter
- Yellow ASSEMBLY AREA: disc + ring marking on the grass south of the tower,
  with signpost + walkway connecting it to the lobby (evacuation endpoint)

**Interior (per floor):**
- Lobby: reception + logo wall, waiting lounge, security desk
- Offices (2–4): 12 cubicles w/ chairs & monitors, conference table, filing
- Executive (5): 2 exec offices, boardroom + chairs, kitchenette, lounge
- Hazards: bookshelf, glass partition, ceiling tile, red hazard-zone marker
- Emissive evac signage: green EXIT arrow trail + EXIT sign toward stairwell,
  blue stair markers + step nosings (matches the SVG map palette)

**Materials (evac_art.py):** `Evac_CurtainGlass` (alpha 0.72, metal 0.3),
`Evac_Mullion`, `Evac_Spandrel`, `Evac_Roof`, `Evac_Grass`, `Evac_Pavement`,
plus prior `Evac_Wall/Carpet/Wood/Fabric/Metal*` and emissive
`Evac_ExitGreen/StairBlue/HazardRed/AssemblyYellow`.

**Sizes:** OfficeBuilding_5F.fbx = 214 KB, OfficeBuilding_5F_Exterior.fbx =
214 KB, floors 44–50 KB each (blockout was ~19–22 KB).

**Deliverable added:** `Building/OfficeBuilding_5F_Exterior.fbx` (shell +
ground/grass/plaza/assembly for context placement).

---

## Phase 3: Unity Import Verification

**Tool:** `EvacuaideBatch.ImportAndVerify` (batchmode)  
**Result:** 0 failures  
**Verified:**
- All 20 FBX imported (20 `.fbx.meta` files)
- XR packages resolved: `com.unity.xr.interaction.toolkit`, `com.unity.xr.openxr`, `com.unity.vectorgraphics` in `packages-lock.json`
- `Assets/Evacuaide/Evacuaide.unity` scene built and saved (59KB)
- Building has 6 MeshRenderers (5 floors + signage)

---

## Phase 4: Android/Quest APK Build

**Tool:** `EvacuaideBuild.BuildQuestApk` (batchmode, `-buildTarget Android`)  
**Result:** PASS

| Item | Value |
|---|---|
| APK | `EvacuaideVR/Builds/Evacuaide_Quest.apk` |
| Size | 21 MB (391,880,999 bytes) |
| Build time | 14 min 20 s |
| Target | Android ARM64, IL2CPP, min API 29 |
| Package ID | `com.evacuaide.vr` |
| Unity version | 2022.3.62f1 |
| XR | OpenXR, Oculus Touch Controller Profile, activeInputHandler=Both |

**Environment assembled during build phase:**
- AndroidPlayer build support: standalone target installer from Unity CDN
- JDK 11: Unity's own OpenJDK 11.0.14.1 extracted to `%LOCALAPPDATA%\EvacuaideJDK11`
- NDK r23b: extracted to `<SDK>\ndk\android-ndk-r23b`
- cmdline-tools 6.0: placed at `<SDK>\cmdline-tools\latest`
- SDK: existing Android Studio SDK at `%LOCALAPPDATA%\Android\Sdk`
- OpenXR: OculusTouchControllerProfile enabled via direct YAML edit to `OpenXRPackageSettings.asset`
- Loader: assigned via `XRPackageMetadataStore.AssignLoader` (EvacuaideXRSetup.cs)

---

## Deliverables

```
Evacuaide_Assets_Rhenmart/
├── Building/  OfficeBuilding_5F.fbx (144KB, art-passed)
├── Floors/    5x .fbx (PBR materials, glass facade)
├── Hazards/   5x .fbx (_Pre + _Post states each)
├── Equipment/ 4x .fbx (VR grab scale, GrabPoint empties)
├── EvacuationMaps/ 5x .svg (bilingual, MANILA INNOVATIONS TOWER)
├── Animations/ 5x .fbx (baked 30fps, 5s each)
└── QA_REPORT.md (87/87)

EvacuaideVR/ (Unity 2022.3.62f1 project)
├── Assets/Evacuaide/ (all FBX + SVG + Editor/Runtime scripts)
├── Packages/manifest.json (XRI, OpenXR, VectorGraphics)
├── Assets/XR/Settings/ (OpenXR configured, Oculus Touch profile enabled)
├── Builds/Evacuaide_Quest.apk ✅ 21MB
└── UNITY_BUILD_REPORT.txt (PASS)
```
