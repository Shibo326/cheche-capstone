// EVACUAIDE - Batch entry points for headless Unity runs
// ======================================================
// Invoked via:
//   Unity.exe -batchmode -quit -projectPath <proj> -executeMethod EvacuaideBatch.ImportAndVerify -logFile <log>
//
// Runs the importer, builds the scene, then writes a QA summary and forces
// a non-zero exit if anything essential is missing.

#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

public static class EvacuaideBatch
{
    const string ROOT = "Assets/Evacuaide";
    const string SCENE = "Assets/Evacuaide/Evacuaide.unity";

    public static void ImportAndVerify()
    {
        int failures = 0;

        // 1) Confirm all expected assets exist as importable models/sprites.
        string[] expectedFbx = {
            "Building/OfficeBuilding_5F", "Floors/Floor_01_Lobby",
            "Floors/Floor_02_Office", "Floors/Floor_03_Office",
            "Floors/Floor_04_Office", "Floors/Floor_05_Executive",
            "Hazards/Bookshelf_Fall", "Hazards/CeilingTile_Crack",
            "Hazards/GlassPartition_Break", "Hazards/FilingCabinet_Topple",
            "Hazards/ElectricalPanel_Spark", "Equipment/Flashlight",
            "Equipment/EmergencyBag", "Equipment/FirstAidKit",
            "Equipment/FireExtinguisher", "Animations/EvacPath_Floor01",
            "Animations/EvacPath_Floor02", "Animations/EvacPath_Floor03",
            "Animations/EvacPath_Floor04", "Animations/EvacPath_Floor05",
        };
        foreach (var rel in expectedFbx)
        {
            string path = $"{ROOT}/{rel}.fbx";
            var go = AssetDatabase.LoadAssetAtPath<GameObject>(path);
            if (go == null) { Debug.LogError($"[QA] Missing model: {path}"); failures++; }
        }

        // 2) Configure importers + build scene.
        try { EvacuaideImporter.ConfigureFbxImporters(); }
        catch (Exception e) { Debug.LogError($"[QA] Importer config failed: {e.Message}"); failures++; }

        // 3) Create and save a scene with the building placed.
        try
        {
            var scene = EditorSceneManager.NewScene(NewSceneSetup.DefaultGameObjects,
                                                    NewSceneMode.Single);
            EvacuaideImporter.BuildScene();
            EditorSceneManager.SaveScene(scene, SCENE);
            Debug.Log($"[QA] Scene saved: {SCENE}");
        }
        catch (Exception e) { Debug.LogError($"[QA] Scene build failed: {e.Message}"); failures++; }

        // 4) Verify the building instance actually has renderers (geometry loaded).
        var building = AssetDatabase.LoadAssetAtPath<GameObject>(
            $"{ROOT}/Building/OfficeBuilding_5F.fbx");
        if (building != null)
        {
            int rc = building.GetComponentsInChildren<MeshRenderer>(true).Length;
            Debug.Log($"[QA] Building MeshRenderers: {rc}");
            if (rc == 0) { Debug.LogError("[QA] Building has no renderers"); failures++; }
        }

        // 5) Write report.
        string report = Path.Combine(Directory.GetCurrentDirectory(), "UNITY_QA_REPORT.txt");
        File.WriteAllText(report,
            $"Evacuaide Unity QA\nTimestamp: {DateTime.Now}\nFailures: {failures}\n" +
            (failures == 0 ? "STATUS: PASS\n" : "STATUS: FAIL\n"));
        Debug.Log($"[QA] Report: {report} (failures={failures})");

        AssetDatabase.SaveAssets();
        if (failures > 0)
            EditorApplication.Exit(1);
    }
}
#endif
