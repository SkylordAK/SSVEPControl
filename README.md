# SSVEP Control — EEG Brain-Computer Interface

This project implements a BCI (Brain-Computer Interface) controller using Steady-State Visually Evoked Potentials (SSVEP). It allows users to make selections or trigger commands simply by focusing on flickering visual stimuli.

## How it Works
When a user focuses on a light flickering at a specific frequency (e.g., 10Hz), the brain's visual cortex generates a neural response at that same frequency. This system detects those responses in real-time using high-resolution FFT analysis.

## Features
- **High-Resolution FFT**: Uses a 3.0-second sliding window for 0.33Hz bin resolution.
- **SNR Verification**: Implements Signal-to-Noise Ratio (SNR) checking to ensure detections are genuine and not background noise.
- **Stability Hysteresis**: Uses a temporal buffer to prevent "flickering" selections and ensure solid command locking.
- **Multi-Target Support**: Default configuration supports four targets (TOP, LEFT, RIGHT, BOTTOM).

## Target Frequencies
- **TOP**: 15.0 Hz
- **LEFT**: 10.0 Hz
- **RIGHT**: 12.0 Hz
- **BOTTOM**: 7.0 Hz

## Setup
1. **EEG Source**: Muse S or Muse 2 headband.
2. **Streaming**: Stream data via OSC to port `5239`.
3. **Stimulator**: Run a visual stimulator (like `ssvep_stimulator.py`) to provide the flickering targets.
4. **Detector**:
   ```bash
   python ssvep_detector.py
   ```

## Integration
The detector sends selection commands over OSC to port `5240` at address `/select`, making it easy to integrate with games, robots, or automation software.
