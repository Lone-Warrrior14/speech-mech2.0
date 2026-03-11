import speech_recognition as sr
import time

def test_auto():
    from speech_to_text import _BT_DEVICE_INDEX
    mic = sr.Microphone(device_index=_BT_DEVICE_INDEX)
    mic.__enter__()
    
    r = sr.Recognizer()
    r.pause_threshold = 1.0
    r.dynamic_energy_threshold = True
    r.dynamic_energy_ratio = 4.0 # Try 4x average noise
    
    print("Adjusting...")
    r.adjust_for_ambient_noise(mic, duration=2.0)
    print("New threshold:", r.energy_threshold)
    
    try:
        t0 = time.time()
        print("Listening...")
        r.listen(mic, timeout=3.0, phrase_time_limit=5.0)
        print("Wait! Captured something, meaning threshold is too low! Time elapsed:", time.time() - t0)
    except sr.WaitTimeoutError:
        print("Success! Ignored background noise!")
        
    mic.__exit__(None, None, None)

if __name__ == "__main__":
    test_auto()
