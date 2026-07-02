# SSVEPControl — Brain-Computer Interface via SSVEP

A real-time Brain-Computer Interface (BCI) that uses **Steady-State Visually Evoked Potentials (SSVEP)** to detect which flickering stimulus a user is visually attending to, then maps that neural response to a control action.

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python) ![BrainFlow](https://img.shields.io/badge/BrainFlow-5.x-00A86B) ![NumPy](https://img.shields.io/badge/NumPy-1.26-013243?logo=numpy)

---

## What is SSVEP?

When you look at a flickering light at a specific frequency (e.g. 10 Hz), your visual cortex generates an EEG signal at exactly that frequency. SSVEP BCIs exploit this: present multiple stimuli at different frequencies, then use FFT to identify the dominant frequency in the occipital EEG signal — that is the stimulus the user is focused on.

---

## How It Works

```
EEG headset (BrainFlow / OSC)
        |
ssvep_detector.py
        |
  FFT on O1/O2 (occipital) channels
        |
  SNR scored at 10 Hz, 12 Hz, 15 Hz
        |
  Winner-history smoothing buffer (thread-safe)
        |
  Control action dispatched
```

---

## Features

- **3 target frequencies** — 10 Hz, 12 Hz, 15 Hz (configurable)
- **SNR-based detection** — minimum SNR threshold of 2.5, using 3 noise bins each side of the target frequency
- **Winner-history buffer** — smooths noisy classifications over a sliding window
- **Thread-safe state** — `threading.Lock` guards all shared reads/writes
- **OSC input** — receives EEG data via OSC protocol (compatible with Muse S, OpenBCI, etc.)

---

## Getting Started

### Prerequisites

- Python 3.9+
- EEG headset supported by BrainFlow (Muse S, OpenBCI Cyton, etc.) — or BrainFlow synthetic board for testing
- OSC-compatible streamer (e.g. mind-monitor for Muse S)

### Installation

```bash
git clone https://github.com/SkylordAK/SSVEPControl.git
cd SSVEPControl
pip install -r requirements.txt
```

### Run

```bash
python ssvep_detector.py
```

---

## Configuration

Edit the constants at the top of `ssvep_detector.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `TARGET_FREQS` | `[10, 12, 15]` | SSVEP stimulus frequencies in Hz |
| `SNR_THRESHOLD` | `2.5` | Minimum SNR to declare a detection |
| `NOISE_BINS` | `3` | Adjacent bins used for noise floor estimation |
| `HISTORY_LEN` | `5` | Consecutive frames required to lock a target |
| `OSC_PORT` | `5000` | Port to listen for incoming EEG data |

---

## Signal Processing Pipeline

1. Bandpass filter (1–50 Hz) — removes DC drift and high-frequency noise
2. Epoch extraction — sliding window of 1–2 seconds
3. FFT — frequency spectrum of O1/O2 channels
4. SNR calculation — peak bin power vs. mean of surrounding bins
5. Classification — frequency with highest SNR above threshold wins
6. Smoothing — `winner_history` deque; majority vote over last N frames

---

## Requirements

```
brainflow
numpy
scipy
python-osc
```

---

## Related Projects

- [EpilepsyDetection](https://github.com/SkylordAK/EpilepsyDetection) — Real-time multi-pattern seizure detector
- [MindReader](https://github.com/SkylordAK/MindReader) — EEG mental state classifier

---

## Disclaimer

Research and educational project. Not a certified medical device.

## License

MIT
