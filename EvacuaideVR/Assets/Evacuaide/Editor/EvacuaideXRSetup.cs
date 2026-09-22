// EVACUAIDE - XR / OpenXR loader setup for Android (Quest)
// ========================================================
// Assigns the OpenXR loader to the Android build target and enables the
// Meta Quest feature so the OpenXR build preprocessor stops throwing
// "OpenXR Settings found in project but not yet loaded".
//
//   Unity.exe -batchmode -quit -projectPath <p> -executeMethod EvacuaideXRSetup.EnableOpenXRAndroid -logFile <log>

#if UNITY_EDITOR
using System;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEngine;
using UnityEditor.XR.Management;
using UnityEditor.XR.Management.Metadata;
using UnityEngine.XR.Management;

public static class EvacuaideXRSetup
{
    const string OPENXR_LOADER = "UnityEngine.XR.OpenXR.OpenXRLoader";

    const string XR_ASSET =
        "Assets/XR/XRGeneralSettingsPerBuildTarget.asset";

    public static void EnableOpenXRAndroid()
    {
        var perTarget = AssetDatabase.LoadAssetAtPath<XRGeneralSettingsPerBuildTarget>(XR_ASSET);
        if (perTarget == null)
        {
            Debug.LogError($"[XR] Missing {XR_ASSET}. Open XR Plug-in Management once to create it.");
            EditorApplication.Exit(1);
            return;
        }

        // Ensure it's registered as the active XR config object.
        EditorBuildSettings.AddConfigObject(XRGeneralSettings.k_SettingsKey, perTarget, true);

        // Ensure Android general settings + manager exist and are saved into the asset.
        var general = perTarget.SettingsForBuildTarget(BuildTargetGroup.Android);
        if (general == null)
        {
            general = ScriptableObject.CreateInstance<XRGeneralSettings>();
            general.name = "Android XR Settings";
            AssetDatabase.AddObjectToAsset(general, perTarget);
            perTarget.SetSettingsForBuildTarget(BuildTargetGroup.Android, general);
        }
        if (general.Manager == null)
        {
            var mgr = ScriptableObject.CreateInstance<XRManagerSettings>();
            mgr.name = "Android XR Manager";
            AssetDatabase.AddObjectToAsset(mgr, perTarget);
            general.Manager = mgr;
        }
        EditorUtility.SetDirty(perTarget);
        AssetDatabase.SaveAssets();

        // Assign OpenXR loader to Android on the now-persisted manager.
        bool ok = XRPackageMetadataStore.AssignLoader(
            general.Manager, OPENXR_LOADER, BuildTargetGroup.Android);
        Debug.Log($"[XR] AssignLoader OpenXR (Android) -> {ok}");

        TryEnableMetaQuestFeature();

        EditorUtility.SetDirty(general.Manager);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log("[XR] OpenXR Android setup complete.");
    }

    static void TryEnableMetaQuestFeature()
    {
        try
        {
            var settingsType = Type.GetType(
                "UnityEngine.XR.OpenXR.OpenXRSettings, Unity.XR.OpenXR");
            if (settingsType == null) { Debug.LogWarning("[XR] OpenXR assembly not found."); return; }

            // Resolve the ambiguous overload explicitly by parameter type.
            var getForGroup = settingsType.GetMethod("GetSettingsForBuildTargetGroup",
                BindingFlags.Public | BindingFlags.Static, null,
                new[] { typeof(BuildTargetGroup) }, null);
            object settings = getForGroup?.Invoke(null, new object[] { BuildTargetGroup.Android });
            if (settings == null) { Debug.LogWarning("[XR] No OpenXR settings for Android."); return; }

            var getFeatures = settingsType.GetMethod("GetFeatures", Type.EmptyTypes);
            var features = getFeatures?.Invoke(settings, null) as System.Collections.IEnumerable;
            if (features == null) { Debug.LogWarning("[XR] No OpenXR features list."); return; }

            // Enable: an interaction profile (Oculus Touch) + Meta Quest support.
            // OpenXR requires >=1 interaction profile enabled to build.
            string[] wanted = {
                "OculusTouchControllerProfile",
                "MetaQuestTouchProControllerProfile",
                "MetaQuestFeature", "OculusQuestFeature",
            };
            int enabled = 0;
            var all = new System.Collections.Generic.List<object>();
            foreach (var f in features) all.Add(f);
            foreach (var f in all)
            {
                var t = f.GetType();
                bool match = wanted.Any(w => t.Name == w) ||
                             (t.Name.Contains("Touch") && t.Name.Contains("Profile"));
                if (match)
                {
                    var enabledProp = t.GetProperty("enabled");
                    if (enabledProp != null && enabledProp.CanWrite)
                    {
                        enabledProp.SetValue(f, true);
                        EditorUtility.SetDirty(f as UnityEngine.Object);
                        enabled++;
                        Debug.Log($"[XR] Enabled OpenXR feature: {t.Name}");
                    }
                }
            }
            // Fallback: if nothing matched, enable the first interaction-profile-like feature.
            if (enabled == 0)
            {
                foreach (var f in all)
                {
                    var t = f.GetType();
                    if (t.Name.Contains("ControllerProfile"))
                    {
                        var p = t.GetProperty("enabled");
                        if (p != null && p.CanWrite) { p.SetValue(f, true); EditorUtility.SetDirty(f as UnityEngine.Object); enabled++; Debug.Log($"[XR] Fallback enabled: {t.Name}"); break; }
                    }
                }
            }
            Debug.Log($"[XR] Enabled {enabled} OpenXR feature(s) total.");
        }
        catch (Exception e) { Debug.LogWarning($"[XR] Meta Quest feature enable failed: {e.Message}"); }
    }
}
#endif
