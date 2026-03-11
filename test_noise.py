import speech_recognition as sr
import time
import audioop
from speech_to_text import _BT_DEVICE_INDEX

m = sr.Microphone(device_index=_BT_DEVICE_INDEX)
m.__enter__()
stream = m.stream

print("Measuring fan noise limits for 5 seconds...")
max_e = 0
t0 = time.time()
while time.time() - t0 < 5:
    d = stream.read(m.CHUNK)
    e = audioop.rms(d, m.SAMPLE_WIDTH)
    max_e = max(max_e, e)

print('Max energy:', max_e)
m.__exit__(None, None, None)
