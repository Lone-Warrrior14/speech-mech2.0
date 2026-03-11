import speech_recognition as sr
import time

def test_fan_noise():
    print("Initialize...")
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 1.0
    recognizer.dynamic_energy_threshold = False
    recognizer.energy_threshold = 4000  

    from speech_to_text import _BT_DEVICE_INDEX
    mic = sr.Microphone(device_index=_BT_DEVICE_INDEX)
    mic.__enter__()
    
    print(f"Mic initialized. Fixed Energy threshold: {recognizer.energy_threshold}")
    
    print("Listening for 15 seconds to see what happens...")
    for i in range(3):
        print(f"\n--- Attempt {i+1} ---")
        try:
            t0 = time.time()
            audio = recognizer.listen(mic, timeout=2.0, phrase_time_limit=5.0)
            elapsed = time.time() - t0
            print(f"Captured audio of length {len(audio.frame_data)} bytes in {elapsed:.2f} seconds.")
            print("Recognizing...")
            text = recognizer.recognize_google(audio)
            print("Heard:", text)
        except sr.WaitTimeoutError:
            print(f"WaitTimeoutError - no speech detected (expected in fan noise if working properly). elapsed: {time.time()-t0:.2f}s")
        except sr.UnknownValueError:
            print("UnknownValueError - could not understand the audio.")
        except Exception as e:
            print("Other error:", e)

if __name__ == "__main__":
    test_fan_noise()
