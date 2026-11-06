import pyaudio

p = pyaudio.PyAudio()

print("\nREALTEK / MICROPHONE INPUT DEVICES\n")

for i in range(p.get_device_count()):

    device = p.get_device_info_by_index(i)

    name = device["name"]
    channels = device["maxInputChannels"]

    if channels > 0:
        if (
            "realtek" in name.lower()
            or "microphone" in name.lower()
        ):
            print(
                f"INDEX: {i}"
            )
            print(
                f"NAME: {name}"
            )
            print(
                f"INPUT CHANNELS: {channels}"
            )
            print("-" * 50)

p.terminate()