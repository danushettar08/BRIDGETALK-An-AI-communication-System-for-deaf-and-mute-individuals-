import pyaudio

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
SECONDS = 5


def main():

    audio = pyaudio.PyAudio()

    try:

        print("=" * 60)
        print("BridgeTalk Microphone Test")
        print("=" * 60)

        default_device = (
            audio.get_default_input_device_info()
        )

        print()
        print("Windows default input:")
        print(
            "Index:",
            default_device["index"]
        )
        print(
            "Name:",
            default_device["name"]
        )
        print(
            "Channels:",
            default_device["maxInputChannels"]
        )
        print(
            "Sample rate:",
            default_device["defaultSampleRate"]
        )

        device_index = int(
            default_device["index"]
        )

        print()
        print(
            "Opening Windows default microphone..."
        )

        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=int(
                default_device[
                    "defaultSampleRate"
                ]
            ),
            input=True,
            input_device_index=device_index,
            frames_per_buffer=CHUNK,
        )

        print(
            "Microphone opened successfully!"
        )

        print()
        print(
            "Speak continuously for "
            f"{SECONDS} seconds."
        )

        for _ in range(
            int(
                int(
                    default_device[
                        "defaultSampleRate"
                    ]
                )
                / CHUNK
                * SECONDS
            )
        ):

            stream.read(
                CHUNK,
                exception_on_overflow=False,
            )

        stream.stop_stream()
        stream.close()

        print()
        print(
            "SUCCESS: microphone stream worked."
        )

    except Exception as exc:

        print()
        print(
            "MICROPHONE ERROR:"
        )

        print(
            repr(exc)
        )

    finally:

        audio.terminate()


if __name__ == "__main__":
    main()