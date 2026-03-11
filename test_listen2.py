import speech_recognition as sr
import time
import pyaudio
import sys

recognizer = sr.Recognizer()
recognizer.energy_threshold = 300
recognizer.dynamic_energy_threshold = True
print("Default energy threshold:", recognizer.energy_threshold)

mic = sr.Microphone()
print("Opening microphone...")
mic.__enter__()

print("Adjusting for ambient noise...")
recognizer.adjust_for_ambient_noise(mic, duration=2)
print("New energy threshold:", recognizer.energy_threshold)

print("\n--- Test 1: Normal listen ---")
print("Say something...")
try:
    audio = recognizer.listen(mic, timeout=5, phrase_time_limit=5)
    print("Heard you! Recognizing...")
    print(recognizer.recognize_google(audio))
except Exception as e:
    print("Error:", e)
    
print("\n--- Test 2: After stop/start stream ---")
if hasattr(mic, 'stream') and mic.stream is not None:
    mic.stream.stop_stream()
    mic.stream.start_stream()
print("Say something again...")
try:
    audio = recognizer.listen(mic, timeout=5, phrase_time_limit=5)
    print("Heard you! Recognizing...")
    print(recognizer.recognize_google(audio))
except Exception as e:
    print("Error:", e)

mic.__exit__(None, None, None)
