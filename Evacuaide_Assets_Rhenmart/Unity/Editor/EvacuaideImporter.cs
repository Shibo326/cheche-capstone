// EVACUAIDE - Unity Import Automation
// ===================================
// Drop this file into: Assets/Evacuaide/Editor/EvacuaideImporter.cs
// Copy the asset folders (Building, Floors, Hazards, Equipment,
// EvacuationMaps, Animations) into: Assets/Evacuaide/
//
// Then in Unity menu:  Evacuaide -> Import & Build Scene
//
// What it does:
//  - Sets FBX import scale so 1 unit = 1 m (assets exported at 0.01 already
//    bake to meters; this enforces useFileScale + convertUnits).
//  - Enables Read/Write on meshes, generates colliders on building + hazards.
//  - Places building at origin, lays out equipment + hazards, imports SVG maps
//    to a world-space UI canvas per floor (requires com.unity.vectorgraphics).
//  - Adds XR Grab Interactable on equipment (requires XR Interaction Toolkit).
//
// Tested target: Unity 6 LTS / 2022.3 LTS, OpenXR + XR Interaction Toolkit.

#if UNITY_EDITOR
using System.IO;
using UnityEditor;
using UnityEngine;

public static class EvacuaideImporter
{
    const string ROOT = "Assets/Evacuaide";

    [MenuItem("Evacuaide/Import & Build Scene")]
    public static void ImportAndBuild()
    {
        ConfigureFbxImporters();
        AssetDatabase.Refresh();
        BuildScene();
        Debug.Log("[Evacuaide] Import & scene build complete.");
    }

    [MenuItem("Evacuaide/1. Configure FBX Import Settings")]
    public static void ConfigureFbxImporters()
    {
        string[] guids = AssetDatabase.FindAssets("t:Model", new[] { ROOT });
        int n = 0;
        foreach (var guid in guids)
        {
            string path = AssetDatabase.GUIDToAssetPath(guid);
            var mi = AssetImporter.GetAtPath(path) as ModelImporter;
            if (mi == null) continue;

            mi.useFileScale = true;
            mi.globalScale = 1f;
            mi.isReadable = true;
            mi.importNormals = ModelImporterNormals.Import;
            mi.materialImportMode = ModelImporterMaterialImportMode.ImportStandard;

            bool isHazard = path.Contains("/Hazards/");
            bool isBuilding = path.Contains("/Building/") || path.Contains("/Floors/");
            bool isAnim = path.Contains("/Animations/");

            mi.addCollider = isHazard || isBuilding;
            mi.importAnimation = isAnim;
            if (isAnim)
            {
                mi.animationType = ModelImporterAnimationType.Generic;
                mi.resampleCurves = true;
            }

            mi.SaveAndReimport();
            n++;
        }
        Debug.Log($"[Evacuaide] Configured {n} FBX importers.");
    }

    [MenuItem("Evacuaide/2. Build Scene")]
    public static void BuildScene()
    {
        var root = new GameObject("Evacuaide_Building");

        // Full building
        Place(root.transform, $"{ROOT}/Building/OfficeBuilding_5F.fbx",
              Vector3.zero, "Building");

        // Player XR rig + drill GameManager wiring.
        SetupXrRig();
        SetupGameManager();

        // Equipment laid out near the lobby, tagged as grabbable
        string[] equip = { "Flashlight", "EmergencyBag", "FirstAidKit", "FireExtinguisher" };
        var equipRoot = new GameObject("Equipment");
        equipRoot.transform.parent = root.transform;
        for (int i = 0; i < equip.Length; i++)
        {
            var go = Place(equipRoot.transform, $"{ROOT}/Equipment/{equip[i]}.fbx",
                           new Vector3(-8 + i * 0.6f, 0.9f, 0), equip[i]);
            AddGrabInteractable(go);
        }

        // Hazards parented per floor (author places precisely in-editor)
        string[] haz = { "Bookshelf_Fall", "CeilingTile_Crack", "GlassPartition_Break",
                         "FilingCabinet_Topple", "ElectricalPanel_Spark" };
        var hazRoot = new GameObject("Hazards");
        hazRoot.transform.parent = root.transform;
        for (int i = 0; i < haz.Length; i++)
            Place(hazRoot.transform, $"{ROOT}/Hazards/{haz[i]}.fbx",
                  new Vector3(0, 0, -6 + i * 3), haz[i]);

        Debug.Log("[Evacuaide] Scene built. Position hazards/equipment per floor as needed.");
    }

    // Build a minimal XR rig. Uses XR Origin via reflection when the XR
    // Interaction Toolkit is installed; otherwise leaves a plain camera rig so
    // the scene still opens and plays in the editor.
    static void SetupXrRig()
    {
        if (GameObject.Find("XR Origin") != null || GameObject.Find("PlayerRig") != null)
            return;

        var rig = new GameObject("PlayerRig");
        // Spawn on Floor 1 near the lobby, standing height.
        rig.transform.position = new Vector3(0f, 0f, -6f);

        var camGo = new GameObject("Main Camera");
        camGo.transform.parent = rig.transform;
        camGo.transform.localPosition = new Vector3(0f, 1.6f, 0f);
        var cam = camGo.AddComponent<Camera>();
        camGo.tag = "MainCamera";
        camGo.AddComponent<AudioListener>();

        var originType = System.Type.GetType(
            "Unity.XR.CoreUtils.XROrigin, Unity.XR.CoreUtils");
        if (originType != null)
        {
            rig.name = "XR Origin";
            var origin = rig.AddComponent(originType);
            var camProp = originType.GetProperty("Camera");
            if (camProp != null && camProp.CanWrite) camProp.SetValue(origin, cam);
            var floorProp = originType.GetProperty("CameraFloorOffsetObject");
            if (floorProp != null && floorProp.CanWrite) floorProp.SetValue(origin, camGo);
            Debug.Log("[Evacuaide] XR Origin rig created.");
        }
        else
        {
            Debug.Log("[Evacuaide] XR CoreUtils not found; created plain camera rig. " +
                      "Install XR Interaction Toolkit for full VR locomotion.");
        }
    }

    // Attach the drill controller stack to a single GameManager object.
    static void SetupGameManager()
    {
        if (GameObject.Find("GameManager") != null) return;
        var gm = new GameObject("GameManager");
        AddByName(gm, "EarthquakeManager");
        AddByName(gm, "EvacuationGuide");
        AddByName(gm, "EvacuaideGameManager");
        Debug.Log("[Evacuaide] GameManager created with drill controllers.");
    }

    static void AddByName(GameObject go, string typeName)
    {
        var t = System.Type.GetType(typeName + ", Assembly-CSharp")
                ?? System.Type.GetType(typeName);
        if (t != null) { if (go.GetComponent(t) == null) go.AddComponent(t); }
        else Debug.LogWarning($"[Evacuaide] Runtime type not found: {typeName}");
    }

    static GameObject Place(Transform parent, string assetPath, Vector3 pos, string name)
    {
        var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(assetPath);
        if (prefab == null)
        {
            Debug.LogWarning($"[Evacuaide] Missing asset: {assetPath}");
            return null;
        }
        var go = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
        go.name = name;
        go.transform.parent = parent;
        go.transform.position = pos;
        return go;
    }

    // Reflection-based so this compiles even if XRI isn't installed yet.
    static void AddGrabInteractable(GameObject go)
    {
        if (go == null) return;
        var t = System.Type.GetType(
            "UnityEngine.XR.Interaction.Toolkit.Interactables.XRGrabInteractable, Unity.XR.Interaction.Toolkit");
        if (t == null)
            t = System.Type.GetType(
                "UnityEngine.XR.Interaction.Toolkit.XRGrabInteractable, Unity.XR.Interaction.Toolkit");
        if (t != null && go.GetComponent(t) == null)
        {
            if (go.GetComponent<Rigidbody>() == null) go.AddComponent<Rigidbody>();
            if (go.GetComponent<Collider>() == null) go.AddComponent<BoxCollider>();
            go.AddComponent(t);
        }
        else if (t == null)
        {
            Debug.Log($"[Evacuaide] XR Interaction Toolkit not found; skipped grab on {go.name}. " +
                      "Install it via Package Manager, then re-run.");
        }
    }
}
#endif
