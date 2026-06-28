# SSVEPControl — Codebase Audit Report

**Audited by:** Claude Sonnet 4.6 (Senior Software Architect mode)
**Date:** 2026-06-28

---

## 1. Project Overview

**Purpose:** Steady-State Visual Evoked Potential (SSVEP) brain-computer interface using a Muse S headset. Detects which flickering visual stimulus the user is focusing on (TOP/LEFT/RIGHT/BOTTOM at 15/10/12/7 Hz) by analyzing FFT SNR, then sends OSC feedback messages for external control.

**Tech Stack:** Python / NumPy / SciPy FFT / pythonosc

**Files:** `ssvep_detector.py`, `ssvep_stimulator.py`, `README.md`, `.gitignore`

---

## 2. Issues Found

### HIGH

#### H-1: Global state (`curr_locked_target`, `winner_history`) is not thread-safe
**File:** `ssvep_detector.py` (lines 32–34)

`curr_locked_target` and `winner_history` are module-level globals accessed by `eeg_handler` which runs in the OSC server's background thread. Without a lock, concurrent reads/writes to `winner_history` (a `deque`) can cause race conditions. Python's GIL provides some protection for simple operations, but compound operations (append + all() check) are not atomic.

**Fix:** Use `threading.Lock()` around reads/writes to `winner_history` and `curr_locked_target`, or move state into a class with a lock.

---

#### H-2: SNR threshold is too low for reliable detection
**File:** `ssvep_detector.py` (line 29)

```python
SNR_THRESHOLD = 1.3    # Ultra-sensitive threshold
```

An SNR of 1.3 means the target frequency only needs to be 30% stronger than surrounding noise to be detected. At this sensitivity, noise artifacts, muscle activity, and eye blinks will frequently produce false positives. The comment "Ultra-sensitive" acknowledges this.

For reliable SSVEP-BCI, SNR thresholds typically need to be 2.0–3.0+, with longer windows (4–8 seconds). This threshold combined with `STABILITY_DEPTH=2` (only 2 consecutive windows needed) is a recipe for frequent false classifications.

---

#### H-3: Noise window for SNR skips only 1 sample on each side of target
**File:** `ssvep_detector.py` (lines 62–64)

```python
noise_vals = np.concatenate([magnitude[max(0, idx-noise_range):idx-1],
                             magnitude[idx+2:idx+noise_range+1]])
```

The noise window excludes `magnitude[idx-1:idx]` on the left (1 sample) and `magnitude[idx]` on the right. This asymmetric skip doesn't account for spectral leakage from the target frequency into its neighbors. Standard practice is to skip 2–3 bins on each side to avoid including leaked energy in the noise estimate.

**Fix:** Skip `idx-3:idx` and `idx+1:idx+4` for better noise estimation.

---

### MEDIUM

#### M-1: `buffer` grows unbounded if window processing falls behind
**File:** `ssvep_detector.py` (line 101)

```python
buffer = np.vstack([buffer, sample])
```

If the EEG handler processes samples faster than the window analysis runs (unlikely for a single channel at 256 Hz, but possible), the buffer will grow without bound. Consider using `deque(maxlen=...)` or trimming the buffer to 2x window size.

---

#### M-2: OSC feedback client always sends to `127.0.0.1:5240`
**File:** `ssvep_detector.py` (lines 79–82)

The feedback target is hardcoded. If `ssvep_stimulator.py` runs on a different machine or port, the integration breaks.

**Fix:** Make `feedback_ip` and `feedback_port` configurable via command-line arguments or environment variables.

---

#### M-3: `analyze_ssvep` averages only TP9 and TP10 channels — ignores frontal channels
**File:** `ssvep_detector.py` (lines 40–43)

Using only occipital channels (TP9, TP10) for SSVEP detection is correct (visual cortex is at the back of the head). However, averaging only 2 channels reduces SNR compared to using all available occipital channels. The Muse S has AF7 and AF8 as frontal channels which correctly should be excluded, but any additional occipital channels should be included.

---

### LOW

#### L-1: No `requirements.txt`

#### L-2: `winner_history.clear()` in `marker_handler` is called from a different thread than `eeg_handler` — potential race condition

---

## 3. Fixes Applied

None — signal processing changes require validation against real EEG hardware.

---

## 4. Recommendations

1. Add a `threading.Lock()` around `winner_history` and `curr_locked_target` access (H-1).
2. Consider raising `SNR_THRESHOLD` to 2.0 and `STABILITY_DEPTH` to 3–5 for fewer false positives (H-2).
3. Improve noise estimation by skipping 2–3 bins on each side (H-3).
4. Make feedback IP/port configurable (M-2).
5. Add `requirements.txt`.
