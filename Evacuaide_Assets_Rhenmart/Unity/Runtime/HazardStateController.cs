// EVACUAIDE - Hazard State Controller (runtime)
// =============================================
// Drop into: Assets/Evacuaide/Runtime/HazardStateController.cs
// Attach to each hazard prefab instance. It finds the "_Pre" and "_Post"
// child meshes inside the imported FBX and swaps them when the earthquake
// triggers. For ElectricalPanel, it also enables the spark VFX anchor.

using UnityEngine;

public class HazardStateController : MonoBehaviour
{
    [Tooltip("Substring identifying the pre-earthquake mesh child.")]
    public string preSuffix = "_Pre";
    [Tooltip("Substring identifying the post-earthquake mesh child.")]
    public string postSuffix = "_Post";
    [Tooltip("Optional child name to enable on trigger (e.g. spark point).")]
    public string sparkChildContains = "SparkPoint";

    [Tooltip("Optional particle system spawned at spark point.")]
    public GameObject sparkVfxPrefab;

    GameObject pre, post, sparkPoint;

    void Awake()
    {
        foreach (var mf in GetComponentsInChildren<Transform>(true))
        {
            var n = mf.name;
            if (n.Contains(preSuffix)) pre = mf.gameObject;
            else if (n.Contains(postSuffix)) post = mf.gameObject;
            if (!string.IsNullOrEmpty(sparkChildContains) && n.Contains(sparkChildContains))
                sparkPoint = mf.gameObject;
        }
        SetTriggered(false);
    }

    /// Call this when the earthquake starts (or per-hazard timing).
    public void SetTriggered(bool triggered)
    {
        if (pre) pre.SetActive(!triggered);
        if (post) post.SetActive(triggered);
        if (sparkPoint) sparkPoint.SetActive(triggered);

        if (triggered && sparkVfxPrefab && sparkPoint)
            Instantiate(sparkVfxPrefab, sparkPoint.transform.position,
                        Quaternion.identity, transform);
    }

    [ContextMenu("Trigger Earthquake State")]
    void DebugTrigger() => SetTriggered(true);
}
