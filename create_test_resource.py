from pathlib import Path

folder = Path("resources/signs/isl/hello")
folder.mkdir(parents=True, exist_ok=True)

test_file = folder / "test.txt"

test_file.write_text(
    "TEMPORARY TEST RESOURCE",
    encoding="utf-8"
)

print("Test resource folder created:")
print(folder)