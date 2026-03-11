import speech_recognition as sr
import time
from speech_to_text import _BT_DEVICE_INDEX

def test_ratios():
    mic = sr.Microphone(device_index=_BT_DEVICE_INDEX)
    mic.__enter__()
    
    for r_val in [2.0, 2.5, 3.0]:
        print(f"\n--- Testing Ratio {r_val} ---")
        recognizer = sr.Recognizer()
        recognizer.pause_threshold = 1.0
        recognizer.dynamic_energy_threshold = True
        recognizer.dynamic_energy_ratio = r_val
        
        print("Calibrating...")
        recognizer.adjust_for_ambient_noise(mic, duration=2.0)
        print("Threshold set to:", recognizer.energy_threshold)
        
        print("Listening for 5 seconds...")
        for i in range(2):
            try:
                t0 = time.time()
                audio = recognizer.listen(mic, timeout=2.0, phrase_time_limit=4.0)
                elapsed = time.time() - t0
                print(f"Captured audio! Length {len(audio.frame_data)} bytes in {elapsed:.1f}s")
                try:
                    text = recognizer.recognize_google(audio)
                    print(f"Heard: {text}")
                except sr.UnknownValueError:
                    print("Could not understand audio.")
            except sr.WaitTimeoutError:
                print("WaitTimeout (No speech detected - Ignored fan noise)")
            except Exception as e:
                print("Error:", e)

    mic.__exit__(None, None, None)

if __name__ == "__main__":
    test_ratios()
