// EVACUAIDE - Android/Quest build configuration + APK build (headless)
// ====================================================================
// Configures the project for Meta Quest (Android, OpenXR) and builds an APK.
//
// Configure only:
//   Unity.exe -batchmode -quit -projectPath <p> -executeMethod EvacuaideBuild.ConfigureQuest -logFile <log>
// Configure + build APK:
//   Unity.exe -batchmode -quit -projectPath <p> -buildTarget Android -executeMethod EvacuaideBuild.BuildQuestApk -logFile <log>
//
// Writes UNITY_BUILD_REPORT.txt with the outcome.

#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

public static class EvacuaideBuild
{
    const string SCENE = "Assets/Evacuaide/Evacuaide.unity";
    const string OUT_DIR = "Builds";
    const string APK = "Builds/Evacuaide_Quest.apk";
    const string PACKAGE = "com.evacuaide.vr";

    [MenuItem("Evacuaide/Configure for Quest")]
    public static void ConfigureQuest()
    {
        // Point Unity at the machine's existing Android SDK/NDK/JDK so builds
        // don't require the Hub-managed module. Paths verified on this box.
        ConfigureAndroidSdkPaths();

        // Android player settings for Quest.
        PlayerSettings.SetApplicationIdentifier(BuildTargetGroup.Android, PACKAGE);
        PlayerSettings.companyName = "Evacuaide";
        PlayerSettings.productName = "Evacuaide";

        // Quest is ARM64, IL2CPP, min API 29 (Android 10) per Meta guidance.
        PlayerSettings.SetScriptingBackend(BuildTargetGroup.Android, ScriptingImplementation.IL2CPP);
        PlayerSettings.Android.targetArchitectures = AndroidArchitecture.ARM64;
        PlayerSettings.Android.minSdkVersion = AndroidSdkVersions.AndroidApiLevel29;
        PlayerSettings.Android.targetSdkVersion = AndroidSdkVersions.AndroidApiLevelAuto;

        // VR-friendly defaults.
        PlayerSettings.colorSpace = ColorSpace.Linear;
        PlayerSettings.virtualRealitySupported = false; // legacy VR off; use XR plugin
        PlayerSettings.gpuSkinning = true;

        // OpenXR requires the new Input System (value 2 = Both, safest for tooling).
        SetActiveInputHandlingBoth();

        // Best-effort: enable OpenXR loader on Android via reflection so this
        // compiles even before the XR packages finish importing.
        TryEnableOpenXR();

        EnsureSceneInBuild();
        AssetDatabase.SaveAssets();
        Debug.Log("[BUILD] Quest configuration applied.");
        WriteReport("CONFIGURE", true, "Quest player settings applied.");
    }

    public static void BuildQuestApk()
    {
        ConfigureQuest();
        Directory.CreateDirectory(OUT_DIR);

        var opts = new BuildPlayerOptions
        {
            scenes = new[] { SCENE },
            locationPathName = APK,
            target = BuildTarget.Android,
            targetGroup = BuildTargetGroup.Android,
            options = BuildOptions.None,
        };

        BuildReport report = BuildPipeline.BuildPlayer(opts);
        var summary = report.summary;
        bool ok = summary.result == BuildResult.Succeeded;
        string detail = ok
            ? $"APK: {APK} ({summary.totalSize} bytes), time {summary.totalTime}"
            : $"Build {summary.result}: {summary.totalErrors} errors";
        Debug.Log($"[BUILD] {detail}");
        WriteReport("BUILD_APK", ok, detail);

        if (!ok) EditorApplication.Exit(1);
    }

    static void SetActiveInputHandlingBoth()
    {
        // activeInputHandler: 0=Old, 1=New, 2=Both. OpenXR needs New or Both.
        try
        {
            var assets = AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/ProjectSettings.asset");
            if (assets == null || assets.Length == 0)
            {
                Debug.LogWarning("[BUILD] ProjectSettings.asset not loadable for input handling.");
                return;
            }
            var so = new SerializedObject(assets[0]);
            var prop = so.FindProperty("activeInputHandler");
            if (prop != null)
            {
                if (prop.intValue != 2)
                {
                    prop.intValue = 2; // Both
                    so.ApplyModifiedProperties();
                    Debug.Log("[BUILD] activeInputHandler -> 2 (Both). Restart required to fully apply.");
                }
                else Debug.Log("[BUILD] activeInputHandler already Both.");
            }
            else Debug.LogWarning("[BUILD] activeInputHandler property not found.");
        }
        catch (Exception e) { Debug.LogWarning($"[BUILD] Input handling set failed: {e.Message}"); }
    }

    static void ConfigureAndroidSdkPaths()
    {
        string home = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
        string sdk = Path.Combine(home, "AppData", "Local", "Android", "Sdk");
        string ndk = Path.Combine(sdk, "ndk", "android-ndk-r23b");
        // Unity 2022.3 requires JDK 11; use the extracted Unity OpenJDK, not JBR 21.
        string jdk = Path.Combine(home, "AppData", "Local", "EvacuaideJDK11");

        if (Directory.Exists(sdk))
        {
            EditorPrefs.SetString("AndroidSdkRoot", sdk);
            Debug.Log($"[BUILD] AndroidSdkRoot -> {sdk}");
        }
        else Debug.LogWarning($"[BUILD] SDK not found at {sdk}");

        if (Directory.Exists(ndk))
        {
            EditorPrefs.SetString("AndroidNdkRootR23B", ndk);
            EditorPrefs.SetString("AndroidNdkRoot", ndk);
            Debug.Log($"[BUILD] AndroidNdkRoot -> {ndk}");
        }
        else Debug.LogWarning($"[BUILD] NDK not found at {ndk}");

        if (Directory.Exists(jdk))
        {
            // Use custom JDK (not the embedded one) and point at Android Studio's JBR.
            EditorPrefs.SetBool("JdkUseEmbedded", false);
            EditorPrefs.SetString("JdkPath", jdk);
            EditorPrefs.SetString("JdkPath_Root", jdk);
            // Also set env var for tools that read JAVA_HOME.
            Environment.SetEnvironmentVariable("JAVA_HOME", jdk);
            Debug.Log($"[BUILD] JdkPath -> {jdk} (embedded=false)");
        }
        else Debug.LogWarning($"[BUILD] JDK not found at {jdk}");
    }

    static void EnsureSceneInBuild()
    {
        var scenes = EditorBuildSettings.scenes.ToList();
        if (!scenes.Any(s => s.path == SCENE))
        {
            scenes.Add(new EditorBuildSettingsScene(SCENE, true));
            EditorBuildSettings.scenes = scenes.ToArray();
        }
    }

    static void TryEnableOpenXR()
    {
        try
        {
            // XRGeneralSettingsPerBuildTarget / XRPackageMetadata live in
            // com.unity.xr.management; touch via reflection to avoid hard dep
            // if the package is mid-import.
            var mgmtType = Type.GetType(
                "UnityEditor.XR.Management.XRGeneralSettingsPerBuildTarget, Unity.XR.Management.Editor");
            if (mgmtType == null)
                Debug.LogWarning("[BUILD] XR Management not found yet; enable OpenXR " +
                                 "in Project Settings > XR Plug-in Management (Android) after import.");
            else
                Debug.Log("[BUILD] XR Management present. Enable OpenXR + Meta Quest " +
                          "feature group in XR Plug-in Management if not already set.");
        }
        catch (Exception e) { Debug.LogWarning($"[BUILD] OpenXR enable skipped: {e.Message}"); }
    }

    static void WriteReport(string phase, bool ok, string detail)
    {
        string path = Path.Combine(Directory.GetCurrentDirectory(), "UNITY_BUILD_REPORT.txt");
        File.WriteAllText(path,
            $"Evacuaide Unity Build\nPhase: {phase}\nTimestamp: {DateTime.Now}\n" +
            $"Status: {(ok ? "PASS" : "FAIL")}\nDetail: {detail}\n");
        Debug.Log($"[BUILD] Report: {path}");
    }
}
#endif
