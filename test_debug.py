import speech_recognition as sr
import time
from speech_to_text import get_global_mic, recognizer

def test_mic_debug():
    print("Init global mic...")
    mic = get_global_mic()
    print("Mic initiated. Energy threshold:", recognizer.energy_threshold)
    
    print("\nPlease say something right now...")
    for i in range(5):
        try:
            print(f"[{i}] Listening...")
            t0 = time.time()
            audio = recognizer.listen(mic, timeout=2.0, phrase_time_limit=5.0)
            elapsed = time.time() - t0
            print(f"[{i}] Audio captured ({len(audio.frame_data)} bytes) in {elapsed:.1f}s")
            
            try:
                print(f"[{i}] Recognizing...")
                text = recognizer.recognize_google(audio)
                print(f"[{i}] Text: {text}")
                break # We got it!
            except sr.UnknownValueError:
                print(f"[{i}] Could not understand audio.")
        except sr.WaitTimeoutError:
            print(f"[{i}] Wait timeout. No speech detected.")
        except Exception as e:
            print(f"[{i}] Error: {e}")

if __name__ == "__main__":
    test_mic_debug()
