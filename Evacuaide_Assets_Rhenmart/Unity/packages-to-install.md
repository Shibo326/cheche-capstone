# Evacuaide — Unity Packages Required

Install these via **Window → Package Manager** (or add to `Packages/manifest.json`)
in your Unity project before running `Evacuaide → Import & Build Scene`.

## Recommended editor
- Unity **6 LTS** or **2022.3 LTS** (install through Unity Hub).
- Build target: **Android** (Meta Quest).

## manifest.json dependencies (add these lines)
```json
{
  "dependencies": {
    "com.unity.xr.interaction.toolkit": "3.0.7",
    "com.unity.xr.openxr": "1.11.0",
    "com.unity.xr.management": "4.5.0",
    "com.unity.vectorgraphics": "2.0.0-preview.24"
  }
}
```

## After install
1. **Project Settings → XR Plug-in Management → Android tab** → enable **OpenXR**.
2. In **OpenXR** feature groups, enable **Meta Quest Support** and your
   controller/hand-interaction profile.
3. `com.unity.vectorgraphics` lets you import the `EvacuationMaps/*.svg`
   as sprites for world-space UI canvases (one per floor).
4. Run **Evacuaide → Import & Build Scene**.

> Package versions above are known-good starting points. If Package Manager
> offers a newer verified version for your editor, prefer that.
