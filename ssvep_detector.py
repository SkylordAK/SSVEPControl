"""
SSVEP Detector — Stable FFT Analysis
Connects to Muse S via OSC.

IMPROVEMENTS:
- 3.0s window for higher frequency resolution.
- Stability buffer (hysteresis) to prevent flickering selections.
- Multi-target SNR verification.
"""

import sys
import numpy as np
from pythonosc import dispatcher, osc_server, udp_client
from scipy.fft import rfft, rfftfreq
from collections import deque

# ──────────────────────── CONFIG ────────────────────────
FS = 256
CHANNELS = 4
WINDOW_SEC = 3.0  # Increased for better resolution (0.33 Hz bin size)
WINDOW_SAMPLES = int(FS * WINDOW_SEC)
OVERLAP = 0.8     # High overlap for smooth updates
STEP_SAMPLES = int(WINDOW_SAMPLES * (1 - OVERLAP))

TARGET_FREQS = [15.0, 10.0, 12.0, 7.0]
TARGET_LABELS = ["TOP", "LEFT", "RIGHT", "BOTTOM"]

STABILITY_DEPTH = 2  # Reduced for faster response
SNR_THRESHOLD = 1.3    # Ultra-sensitive threshold

# Buffer for stability
winner_history = deque(maxlen=STABILITY_DEPTH)
curr_locked_target = "None"

def analyze_ssvep(window):
    """
    Find which target frequency has the highest SNR.
    """
    # Use TP9 (0) and TP10 (3)
    eeg_data = window[:, [0, 3]] 
    # Detrend to remove DC offset/drifts
    eeg_data = eeg_data - np.mean(eeg_data, axis=0)
    avg_signal = np.mean(eeg_data, axis=1) 
    
    yf = rfft(avg_signal)
    xf = rfftfreq(WINDOW_SAMPLES, 1/FS)
    magnitude = np.abs(yf)
    
    best_target = None
    max_snr = 0
    results = {}

    for i, target_f in enumerate(TARGET_FREQS):
        # Find exact index
        idx = np.argmin(np.abs(xf - target_f))
        
        # Power at target
        target_val = magnitude[idx]
        
        # Noise around target (skip immediate neighbors to allow for spectral leakage)
        noise_range = 6
        noise_vals = np.concatenate([magnitude[max(0, idx-noise_range):idx-1], 
                                    magnitude[idx+2:idx+noise_range+1]])
        noise_avg = np.mean(noise_vals) if len(noise_vals) > 0 else 1.0
        
        snr = target_val / noise_avg
        results[TARGET_LABELS[i]] = snr
        
        if snr > SNR_THRESHOLD and snr > max_snr:
            max_snr = snr
            best_target = TARGET_LABELS[i]
            
    return best_target, results

def run_live():
    global curr_locked_target
    ip = '0.0.0.0'
    port = 5239
    feedback_ip = '127.0.0.1'
    feedback_port = 5240
    
    client = udp_client.SimpleUDPClient(feedback_ip, feedback_port)
    buffer = np.empty((0, CHANNELS))
    recording = True  # AUTO-START ENABLED
    data_received = False
    
    print("=" * 60)
    print("  ULTRA-SENSITIVE SSVEP DETECTOR — Muse S")
    print("  (Auto-starting. No Marker 1 required!)")
    print("=" * 60)

    def eeg_handler(address, *args):
        nonlocal buffer, recording, data_received
        global curr_locked_target
        if not data_received:
            print(">>> [SUCCESS] Receiving EEG data from Muse S!")
            data_received = True

        if not recording: return
        
        sample = np.array(args[:CHANNELS]).reshape(1, CHANNELS)
        buffer = np.vstack([buffer, sample])
        
        if buffer.shape[0] >= WINDOW_SAMPLES:
            window = buffer[:WINDOW_SAMPLES]
            buffer = buffer[STEP_SAMPLES:]
            
            winner, snrs = analyze_ssvep(window)
            winner_history.append(winner)
            
            # --- STABILITY LOGIC ---
            new_lock = curr_locked_target # Default to current
            if len(winner_history) == STABILITY_DEPTH and all(x == winner_history[0] for x in winner_history):
                new_lock = winner_history[0] if winner_history[0] is not None else "None"

            if new_lock != curr_locked_target:
                curr_locked_target = new_lock
                client.send_message("/select", curr_locked_target)
                if curr_locked_target != "None":
                    print(f"\n\033[92m[LOCKED] Target: {curr_locked_target}\033[0m")
                else:
                    print("\n[LOST] Target lost.")

            # Real-time console update
            snr_str = " | ".join([f"{l}: {s:.1f}" for l, s in snrs.items()])
            print(f"Status: {curr_locked_target: <6} | {snr_str}", end='\r')

    def marker_handler(address, i):
        nonlocal recording, buffer
        marker = address[-1]
        if marker == "1":
            recording = True
            buffer = np.empty((0, CHANNELS))
            winner_history.clear()
            print("\n🟢 Monitoring STARTED!\n")
        elif marker == "2":
            recording = False
            print("\n🔴 Monitoring STOPPED.\n")
            server.shutdown()

    disp = dispatcher.Dispatcher()
    disp.map("/muse/eeg", eeg_handler)
    disp.map("/eeg", eeg_handler)
    disp.map("/Marker/*", marker_handler)

    server = osc_server.ThreadingOSCUDPServer((ip, port), disp)
    print(f"Listening on port {port}. Feedback to {feedback_port}.")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nExit.")

if __name__ == "__main__":
    run_live()
