// EVACUAIDE - Earthquake Manager (runtime)
// ========================================
// Orchestrates the earthquake event for the VR drill:
//   - Shakes the XR rig / camera with a decaying Perlin-noise motion.
//   - Triggers every HazardStateController in the scene (pre -> post state).
//   - Broadcasts start/stop so guidance UI, audio and scoring can react.
//
// Drop into: Assets/Evacuaide/Runtime/EarthquakeManager.cs
// Attach to a single "GameManager" object. Assign the XR rig transform (or it
// auto-finds the main camera's top-most parent).

using System;
using System.Collections;
using UnityEngine;

public class EarthquakeManager : MonoBehaviour
{
    [Header("Shake target (XR rig root). Auto-detected if left empty.")]
    public Transform shakeTarget;

    [Header("Timing (seconds)")]
    [Tooltip("Delay after Begin() before the shaking starts.")]
    public float warningLead = 3f;
    [Tooltip("How long the ground shakes.")]
    public float quakeDuration = 20f;

    [Header("Shake intensity")]
    [Tooltip("Peak positional shake in metres.")]
    public float maxPositionAmplitude = 0.18f;
    [Tooltip("Peak rotational shake in degrees.")]
    public float maxRotationAmplitude = 1.6f;
    public float shakeFrequency = 8f;

    [Header("Audio (optional)")]
    public AudioSource rumbleSource;

    public event Action OnQuakeStarted;
    public event Action OnQuakeEnded;

    public bool QuakeActive { get; private set; }

    Vector3 _baseLocalPos;
    Quaternion _baseLocalRot;
    float _seed;

    void Awake()
    {
        if (shakeTarget == null)
        {
            var cam = Camera.main;
            if (cam != null)
            {
                // Shake the rig root (top-most parent) so tracking still works.
                var t = cam.transform;
                while (t.parent != null) t = t.parent;
                shakeTarget = t;
            }
        }
        _seed = UnityEngine.Random.value * 100f;
    }

    /// Kick off the full sequence: warning -> shake -> settle.
    public void Begin()
    {
        StopAllCoroutines();
        StartCoroutine(QuakeRoutine());
    }

    IEnumerator QuakeRoutine()
    {
        if (warningLead > 0f) yield return new WaitForSeconds(warningLead);

        if (shakeTarget != null)
        {
            _baseLocalPos = shakeTarget.localPosition;
            _baseLocalRot = shakeTarget.localRotation;
        }

        // Flip every hazard to its post-earthquake state.
        foreach (var h in FindObjectsOfType<HazardStateController>(true))
            h.SetTriggered(true);

        if (rumbleSource != null) { rumbleSource.loop = true; rumbleSource.Play(); }

        QuakeActive = true;
        OnQuakeStarted?.Invoke();

        float t = 0f;
        while (t < quakeDuration)
        {
            t += Time.deltaTime;
            // Envelope: quick ramp-up, long decay, so it feels like a real quake.
            float p = t / quakeDuration;
            float envelope = Mathf.Sin(Mathf.Clamp01(p * 4f) * Mathf.PI * 0.5f)  // ramp in
                             * (1f - Mathf.SmoothStep(0.5f, 1f, p));               // decay out
            ApplyShake(envelope, t);
            yield return null;
        }

        // Settle back to rest.
        if (shakeTarget != null)
        {
            shakeTarget.localPosition = _baseLocalPos;
            shakeTarget.localRotation = _baseLocalRot;
        }
        if (rumbleSource != null) rumbleSource.Stop();

        QuakeActive = false;
        OnQuakeEnded?.Invoke();
    }

    void ApplyShake(float envelope, float time)
    {
        if (shakeTarget == null || envelope <= 0f) return;
        float f = shakeFrequency;
        // Perlin noise in [-1,1] per axis, decorrelated by offset + seed.
        float nx = Mathf.PerlinNoise(_seed + time * f, 0f) * 2f - 1f;
        float ny = Mathf.PerlinNoise(0f, _seed + time * f) * 2f - 1f;
        float nz = Mathf.PerlinNoise(_seed + time * f, _seed + time * f) * 2f - 1f;

        Vector3 posOffset = new Vector3(nx, ny * 0.4f, nz)
                            * (maxPositionAmplitude * envelope);
        Vector3 rotOffset = new Vector3(ny, nx, nz)
                            * (maxRotationAmplitude * envelope);

        shakeTarget.localPosition = _baseLocalPos + posOffset;
        shakeTarget.localRotation = _baseLocalRot * Quaternion.Euler(rotOffset);
    }

    [ContextMenu("Begin Earthquake Now")]
    void DebugBegin() => Begin();
}
