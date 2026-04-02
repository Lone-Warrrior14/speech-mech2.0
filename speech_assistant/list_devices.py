import pyaudio
p = pyaudio.PyAudio()
print("Available INPUT devices:")
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info["maxInputChannels"] > 0:
        name = info["name"]
        ch = info["maxInputChannels"]
        rate = int(info["defaultSampleRate"])
        print(f"  [{i}] {name}  ch={ch}  rate={rate}Hz")
p.terminate()
