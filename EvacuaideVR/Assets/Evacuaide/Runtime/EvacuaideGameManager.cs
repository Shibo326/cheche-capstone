// EVACUAIDE - Game Manager (runtime)
// ==================================
// Top-level drill flow for the earthquake evacuation simulation:
//
//   Briefing  ->  Earthquake  ->  Evacuate  ->  Assembly (results)
//
// It wires EarthquakeManager + EvacuationGuide together, drives simple state
// transitions, and exposes UnityEvents so a world-space UI (briefing text,
// timer, results panel) can hook in without code changes.
//
// Drop into: Assets/Evacuaide/Runtime/EvacuaideGameManager.cs
// Attach to the GameManager object alongside EarthquakeManager + EvacuationGuide.

using System.Collections;
using UnityEngine;
using UnityEngine.Events;

[RequireComponent(typeof(EarthquakeManager))]
[RequireComponent(typeof(EvacuationGuide))]
public class EvacuaideGameManager : MonoBehaviour
{
    public enum Phase { Briefing, Earthquake, Evacuating, Complete }

    [Header("Flow")]
    [Tooltip("Auto-start the drill on scene load.")]
    public bool autoStart = true;
    [Tooltip("Seconds of briefing before the earthquake begins.")]
    public float briefingSeconds = 6f;

    [Header("Events (for UI/audio hooks)")]
    public UnityEvent onBriefing;
    public UnityEvent onEarthquake;
    public UnityEvent onEvacuate;
    public UnityEvent<float> onComplete;   // passes evac time in seconds

    public Phase Current { get; private set; } = Phase.Briefing;

    EarthquakeManager _quake;
    EvacuationGuide _guide;

    void Awake()
    {
        _quake = GetComponent<EarthquakeManager>();
        _guide = GetComponent<EvacuationGuide>();
    }

    void OnEnable()
    {
        _quake.OnQuakeEnded += HandleQuakeEnded;
        _guide.OnReachedAssembly += HandleReachedAssembly;
    }

    void OnDisable()
    {
        _quake.OnQuakeEnded -= HandleQuakeEnded;
        _guide.OnReachedAssembly -= HandleReachedAssembly;
    }

    void Start()
    {
        if (autoStart) StartDrill();
    }

    public void StartDrill()
    {
        StopAllCoroutines();
        StartCoroutine(DrillRoutine());
    }

    IEnumerator DrillRoutine()
    {
        SetPhase(Phase.Briefing);
        onBriefing?.Invoke();
        yield return new WaitForSeconds(briefingSeconds);

        SetPhase(Phase.Earthquake);
        onEarthquake?.Invoke();
        _quake.Begin();
        // EarthquakeManager fires OnQuakeEnded -> HandleQuakeEnded continues flow.
    }

    void HandleQuakeEnded()
    {
        SetPhase(Phase.Evacuating);
        onEvacuate?.Invoke();
        _guide.BeginEvacuation();
    }

    void HandleReachedAssembly(float evacTime)
    {
        SetPhase(Phase.Complete);
        onComplete?.Invoke(evacTime);
        Debug.Log($"[Evacuaide] Drill complete. Evac time: {evacTime:F1}s");
    }

    void SetPhase(Phase p)
    {
        Current = p;
        Debug.Log($"[Evacuaide] Phase -> {p}");
    }
}
