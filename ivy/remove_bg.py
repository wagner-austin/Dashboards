"""Remove light background from Amanda PNG images."""
from PIL import Image
from pathlib import Path


def remove_light_background(img_path: Path, threshold: int = 190) -> None:
    """Make light pixels transparent."""
    img = Image.open(img_path).convert("RGBA")
    data = list(img.getdata())
    new_data = []
    for item in data:
        # If pixel is light (above threshold on all channels), make it transparent
        if item[0] > threshold and item[1] > threshold and item[2] > threshold:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)
    img.putdata(new_data)
    img.save(img_path)
    print(f"Processed: {img_path.name}")


def main() -> None:
    originals = Path(__file__).parent / "originals"
    count = 0
    for folder in originals.iterdir():
        if folder.is_dir() and folder.name.startswith("amanda_"):
            for png in folder.glob("*.png"):
                remove_light_background(png, threshold=185)
                count += 1
    print(f"Total: {count} images processed")


if __name__ == "__main__":
    main()
