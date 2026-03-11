"""
Diagnostic tool to hear how your voice sounds AFTER RNNoise + VAD processing.
Saves two WAV files:
  - raw_recording.wav   : What the microphone hears (raw, before any filter)
  - clean_recording.wav : After RNNoise denoising + VAD speech isolation

Run this file standalone:
  py test_vad_rnnoise.py
"""

import pyaudio
import webrtcvad
import pyrnnoise
import numpy as np
import wave

SAMPLE_RATE = 16000
CHUNK_SIZE  = 480       # 30ms at 16kHz (WebRTC VAD requires 10, 20, or 30ms frames)
RECORD_SECONDS = 8      # How long to record
VAD_AGGRESSIVENESS = 0  # 0=most permissive (fan-noise friendly), 3=harshest. Use 0 for noisy rooms.

# Set to None to auto-detect Bluetooth device, or set a specific index like DEVICE_INDEX = 2
DEVICE_INDEX = None

# Keywords to match Bluetooth devices — "headset" preferred over "hands-free"
# (hands-free/HFP uses 8kHz which is incompatible with 16kHz VAD setup)
BT_PREFERRED = ["headset", "airdopes", "earphone", "buds", "airpods", "bluetooth"]
BT_FALLBACK  = ["hands-free", "handsfree"]

def find_bluetooth_device():
    """Find best working Bluetooth input device at 16kHz."""
    p = pyaudio.PyAudio()
    candidates = []  # list of (priority, index, name)
    
    print("\nScanning audio input devices:")
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info["maxInputChannels"] > 0:
            name = info["name"]
            name_lower = name.lower()
            matched = False
            for kw in BT_PREFERRED:
                if kw in name_lower:
                    candidates.append((0, i, name))  # priority 0 = preferred
                    print(f"  [{i}] {name}  <-- BT HEADSET")
                    matched = True
                    break
            if not matched:
                for kw in BT_FALLBACK:
                    if kw in name_lower:
                        candidates.append((1, i, name))  # priority 1 = fallback
                        print(f"  [{i}] {name}  <-- BT HANDS-FREE (fallback)")
                        matched = True
                        break
            if not matched:
                print(f"  [{i}] {name}")
    p.terminate()

    # Sort by priority, then try each in order — pick first that opens cleanly at 16kHz
    candidates.sort(key=lambda x: x[0])
    for priority, idx, name in candidates:
        try:
            test_p = pyaudio.PyAudio()
            test_s = test_p.open(format=pyaudio.paInt16, channels=1, rate=SAMPLE_RATE,
                                 input=True, input_device_index=idx, frames_per_buffer=480)
            test_s.stop_stream()
            test_s.close()
            test_p.terminate()
            print(f"\nSelected device [{idx}]: {name}")
            return idx
        except Exception as e:
            print(f"  Device [{idx}] failed ({e}), trying next...")
    
    print("\nNo working Bluetooth device found! Using system default.")
    return None

def record_and_save():
    global DEVICE_INDEX
    
    if DEVICE_INDEX is None:
        DEVICE_INDEX = find_bluetooth_device()
    
    print(f"\nInitializing RNNoise + VAD (aggressiveness={VAD_AGGRESSIVENESS}) on device [{DEVICE_INDEX}]...")
    vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)
    rnnoise_filter = pyrnnoise.RNNoise(SAMPLE_RATE)

    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=SAMPLE_RATE,
        input=True,
        input_device_index=DEVICE_INDEX,
        frames_per_buffer=CHUNK_SIZE
    )

    print(f"\nFlushing startup static...")
    for _ in range(10):
        stream.read(CHUNK_SIZE, exception_on_overflow=False)

    print(f"Recording for {RECORD_SECONDS} seconds... SPEAK NOW!\n")

    raw_frames   = []
    clean_frames = []
    speech_detected_count = 0

    total_chunks = int(RECORD_SECONDS * SAMPLE_RATE / CHUNK_SIZE)

    for i in range(total_chunks):
        raw_data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
        raw_np   = np.frombuffer(raw_data, dtype=np.int16)

        # --- VAD check on RAW audio (fan noise tolerant) ---
        is_speech = vad.is_speech(raw_data, SAMPLE_RATE)

        speech_label = "SPEECH" if is_speech else "silence"
        print(f"  Chunk {i+1:4d}/{total_chunks} | {speech_label}", end="\r")

        raw_frames.append(raw_data)     # Always save raw
        if is_speech:
            clean_frames.append(raw_data)  # Only save VAD-selected RAW chunks
            speech_detected_count += 1

    print(f"\n\nDone! Detected speech in {speech_detected_count}/{total_chunks} chunks.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    # Save RAW recording (unfiltered)
    with wave.open("raw_recording.wav", "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b"".join(raw_frames))

    # Save VAD-selected raw frames (before RNNoise)
    if clean_frames:
        with wave.open("vad_selected.wav", "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(b"".join(clean_frames))

        # Now apply RNNoise on the batch of collected speech frames
        print("Applying RNNoise to collected speech batch...")
        raw_concat = np.frombuffer(b"".join(clean_frames), dtype=np.int16)
        denoised_chunks = []
        chunk_size = 480
        for i in range(0, len(raw_concat), chunk_size):
            chunk = raw_concat[i:i+chunk_size]
            if len(chunk) < chunk_size:
                chunk = np.pad(chunk, (0, chunk_size - len(chunk)))
            is_last = (i + chunk_size >= len(raw_concat))
            result = list(rnnoise_filter.denoise_chunk(chunk, partial=is_last))
            if result:
                denoised_chunks.append(result[0][1][0].astype(np.int16))

        if denoised_chunks:
            with wave.open("clean_recording.wav", "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(np.concatenate(denoised_chunks).tobytes())

        print(f"Saved: raw_recording.wav   ({len(raw_frames)} chunks - full mic with fan noise)")
        print(f"Saved: vad_selected.wav    ({len(clean_frames)} chunks - VAD said 'speech', no RNNoise yet)")
        print(f"Saved: clean_recording.wav (RNNoise cleaned version of vad_selected.wav)")
    else:
        print("WARNING: No speech detected at all! Try lowering VAD_AGGRESSIVENESS to 0.")
        print("Saved raw_recording.wav only.")

    print("\nListen order for comparison:")
    print("  1. raw_recording.wav   - raw mic (should hear fan + your voice)")
    print("  2. vad_selected.wav    - only voice chunks VAD chose (fan noise still present)")
    print("  3. clean_recording.wav - RNNoise denoised (fan noise removed)")

if __name__ == "__main__":
    record_and_save()
