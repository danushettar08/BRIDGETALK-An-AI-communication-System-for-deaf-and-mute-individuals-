from services.translation_service import TranslationService


print("BridgeTalk Translation Test")
print("==========================")

service = TranslationService("Kannada")

text = "Hello, how are you?"

print()
print("Original:")
print(text)

print()
print("Translating...")

result = service.translate(text)

print()
print("Translated:")
print(result)

print()
print("Test finished.")