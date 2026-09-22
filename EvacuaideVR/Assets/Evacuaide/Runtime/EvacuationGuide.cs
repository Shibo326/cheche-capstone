// EVACUAIDE - Evacuation Guide (runtime)
// ======================================
// Pulses the green emissive route arrows toward the nearest exit and tracks
// the player's progress to the outdoor assembly point. Reports evacuation
// time and whether the drill was completed safely.
//
// Drop into: Assets/Evacuaide/Runtime/EvacuationGuide.cs
// Attach to the GameManager. It auto-discovers arrow objects by name
// (materials/names containing "Arr" or "Arrow") and the assembly marker
// (name contains "Assembly").

using System;
using System.Collections.Generic;
using UnityEngine;

public class EvacuationGuide : MonoBehaviour
{
    [Header("Discovery")]
    [Tooltip("Name substrings that mark a route-arrow object.")]
    public string[] arrowNameContains = { "Arr", "Arrow", "Route" };
    [Tooltip("Name substring that marks the assembly-point marker.")]
    public string assemblyNameContains = "Assembly";

    [Header("Guidance")]
    [Tooltip("Emissive pulse speed once evacuation is active.")]
    public float pulseSpeed = 2.5f;
    [Tooltip("Distance (m) from the assembly marker counted as 'safe'.")]
    public float assemblyRadius = 4f;

    [Header("Player")]
    [Tooltip("Player head/rig transform. Auto = main camera.")]
    public Transform player;

    public event Action<float> OnReachedAssembly; // passes evac time (s)

    readonly List<Renderer> _arrows = new List<Renderer>();
    readonly List<Material> _arrowMats = new List<Material>();
    Transform _assembly;
    bool _active;
    bool _reached;
    float _startTime;

    void Awake()
    {
        if (player == null && Camera.main != null) player = Camera.main.transform;
        Discover();
        SetArrowsVisible(false);
    }

    void Discover()
    {
        foreach (var r in FindObjectsOfType<Renderer>(true))
        {
            string n = r.gameObject.name;
            if (Contains(n, arrowNameContains))
            {
                _arrows.Add(r);
                // Instance the material so pulsing this arrow doesn't tint others.
                _arrowMats.Add(r.material);
            }
            if (!string.IsNullOrEmpty(assemblyNameContains) &&
                n.IndexOf(assemblyNameContains, StringComparison.OrdinalIgnoreCase) >= 0)
                _assembly = r.transform;
        }
        Debug.Log($"[Evac] Guide found {_arrows.Count} arrows, assembly={(_assembly != null)}");
    }

    static bool Contains(string s, string[] subs)
    {
        foreach (var sub in subs)
            if (s.IndexOf(sub, StringComparison.OrdinalIgnoreCase) >= 0) return true;
        return false;
    }

    /// Called when the earthquake ends and it's time to evacuate.
    public void BeginEvacuation()
    {
        _active = true;
        _reached = false;
        _startTime = Time.time;
        SetArrowsVisible(true);
    }

    void SetArrowsVisible(bool v)
    {
        foreach (var r in _arrows)
            if (r != null) r.enabled = v;
    }

    void Update()
    {
        if (!_active || _reached) return;

        // Pulse arrow emission so the route reads as "follow me".
        float e = 2f + Mathf.PingPong(Time.time * pulseSpeed, 2.5f);
        for (int i = 0; i < _arrowMats.Count; i++)
        {
            var m = _arrowMats[i];
            if (m == null) continue;
            if (m.HasProperty("_EmissionColor"))
            {
                Color baseCol = m.GetColor("_EmissionColor");
                // Normalise then scale so we don't compound each frame.
                Color unit = baseCol.maxColorComponent > 0.001f
                    ? baseCol / baseCol.maxColorComponent : Color.green;
                m.SetColor("_EmissionColor", unit * e);
            }
        }

        // Reached the assembly point?
        if (_assembly != null && player != null)
        {
            Vector3 a = _assembly.position; a.y = 0;
            Vector3 p = player.position; p.y = 0;
            if (Vector3.Distance(a, p) <= assemblyRadius)
            {
                _reached = true;
                float evacTime = Time.time - _startTime;
                Debug.Log($"[Evac] Reached assembly in {evacTime:F1}s");
                OnReachedAssembly?.Invoke(evacTime);
            }
        }
    }

    public bool IsActive => _active && !_reached;
}
