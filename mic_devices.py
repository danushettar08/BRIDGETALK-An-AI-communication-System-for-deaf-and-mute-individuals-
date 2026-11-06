import speech_recognition as sr

print("\nAVAILABLE MICROPHONES:\n")

for index, name in enumerate(
    sr.Microphone.list_microphone_names()
):
    print(f"{index}: {name}")