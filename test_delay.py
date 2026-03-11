import time
import pyaudio

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)

time.sleep(2) # accumulate some audio

print("Frames available:", stream.get_read_available())
t0 = time.time()
stream.stop_stream()
stream.start_stream()
print("Time to stop/start:", time.time() - t0)
print("Frames available after stop/start:", stream.get_read_available())

stream.stop_stream()
stream.close()
p.terminate()
