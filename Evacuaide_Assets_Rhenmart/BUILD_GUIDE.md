# EVACUAIDE — End-to-End Build Guide

VR earthquake-evacuation drill set in a 5-floor office tower that matches the
approved evacuation-map blueprint. This guide covers the fully automated
pipeline from Blender source to a Meta Quest APK — no manual Unity steps.

## What gets produced

| Stage | Output | Location |
|-------|--------|----------|
| Building (Blender) | `OfficeBuilding_5F.fbx`, `OfficeBuilding_5F.glb` | `Evacuaide_Assets_Rhenmart/Building/` |
| Per-floor FBX | `Floor_01..05.fbx` | `Evacuaide_Assets_Rhenmart/Floors/` |
| Floor-plan maps | `Floor_0N_Map.png` | `Evacuaide_Assets_Rhenmart/Renders/FloorMaps/` |
| Unity scene | `Evacuaide.unity` | `EvacuaideVR/Assets/Evacuaide/` |
| Quest build | `Evacuaide_Quest.apk` | `EvacuaideVR/Builds/` |

## One-command build

From `Evacuaide_Assets_Rhenmart/`:

```powershell
powershell -ExecutionPolicy Bypass -File build_all.ps1
```

This runs, in order:

1. **Blender** (`Scripts/run_all.py`) — rebuilds the detailed building from
   `Scripts/building_layout.json`, exports FBX + GLB, renders the 5 floor maps.
2. **Copy** — drops the fresh building + maps into the Unity project.
3. **Unity** — imports & verifies assets, enables OpenXR (Android), builds the
   scene (building + XR rig + drill GameManager), and builds the Quest APK.

Switches:

- `-SkipBlender` — reuse existing exported assets, only run Unity.
- `-SkipUnity` — only run the Blender asset pipeline.
- `-ConfigureOnly` — configure Unity for Quest but skip the APK build.

## The building is data-driven

`Scripts/building_layout.json` is the **single source of truth** — every wall,
room, stairwell, elevator, window, hazard, equipment item and evac sign, with
exact position / size / material. It was extracted from the approved Blender
scene, so `phase2_building.py` reconstructs the building from it 1:1.

To change the layout: edit the JSON (or re-export it from Blender), then re-run
the pipeline. Do not hand-tune geometry in the script.

### Blender scripts

| Script | Role |
|--------|------|
| `evac_art.py` | shared PBR material library |
| `phase2_building.py` | rebuild full building from `building_layout.json` |
| `phase3_hazards.py` | standalone hazard FBX exporter (pre/post states) |
| `phase4_equipment.py` | standalone equipment FBX exporter |
| `phase4_signage.py` | authoring tool for evac arrows / exit signs |
| `phase5_evac_maps.py` | pure-python SVG evacuation maps |
| `phase8_floor_maps.py` | top-down floor-plan PNG renders |
| `phase9_export_glb.py` | Unity-ready GLB + FBX export |
| `run_all.py` | master runner (building → export → maps) |

Run the standalone hazard/equipment FBX exporters too:

```powershell
blender --background --python Scripts/run_all.py --with-asset-exports
```

## The VR drill (Unity runtime)

The scene is playable the moment it opens. `GameManager` carries three
controllers that drive the drill:

- **EarthquakeManager** — warning lead, then a decaying Perlin shake on the XR
  rig; flips every hazard to its post-earthquake state; fires start/end events.
- **EvacuationGuide** — pulses the green route arrows toward the nearest exit,
  detects arrival at the outdoor assembly point, reports the evacuation time.
- **EvacuaideGameManager** — flow: `Briefing → Earthquake → Evacuate →
  Complete`, with `UnityEvent`s for UI/audio hooks.

`HazardStateController` sits on each hazard and swaps `_Pre`/`_Post` meshes.

### Unity Editor menu (manual alternative)

- `Evacuaide/Import & Build Scene` — configure importers + build the scene.
- `Evacuaide/Configure for Quest` — Android/IL2CPP/ARM64/OpenXR player setup.

### Headless entry points

```powershell
$U = "C:\Program Files\Unity\Hub\Editor\2022.3.62f1\Editor\Unity.exe"
$P = "<repo>\EvacuaideVR"
& $U -batchmode -quit -projectPath $P -executeMethod EvacuaideBatch.ImportAndVerify   -logFile $P\unity_import.log
& $U -batchmode -quit -projectPath $P -executeMethod EvacuaideXRSetup.EnableOpenXRAndroid -logFile $P\unity_xr.log
& $U -batchmode -quit -projectPath $P -buildTarget Android -executeMethod EvacuaideBuild.BuildQuestApk -logFile $P\unity_apk.log
```

## Requirements

- **Blender 5.2** at `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`
- **Unity 2022.3.62f1** (matches `EvacuaideVR/ProjectSettings/ProjectVersion.txt`)
- For the APK: Android SDK + NDK (r23b) + JDK 11 — paths are wired in
  `EvacuaideBuild.ConfigureAndroidSdkPaths()`; adjust there if your machine differs.
- Unity packages: XR Interaction Toolkit, OpenXR, XR Management (see
  `Unity/packages-to-install.md`).

## Deploy to a Quest headset

```powershell
adb install -r "<repo>\EvacuaideVR\Builds\Evacuaide_Quest.apk"
```

Reports written after each run:
- `EvacuaideVR/UNITY_QA_REPORT.txt` — asset/scene verification.
- `EvacuaideVR/UNITY_BUILD_REPORT.txt` — APK build outcome + size + time.
