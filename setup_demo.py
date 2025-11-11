# setup_demo.py
import os
from PIL import Image, ImageDraw, ImageFont

def create_dummy_face(name, path):
    """Create a 400×400 white image with the name written in the centre."""
    img = Image.new('RGB', (400, 400), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Use a larger font if available
    try:
        font = ImageFont.truetype("arial.ttf", 60)
    except IOError:
        try:
            font = Image.usedefaultfont
        except:
            font = ImageFont.load_default()

    # --- Use textbbox instead of deprecated textsize ---
    bbox = draw.textbbox((0, 0), name, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    # -------------------------------------------

    x = (400 - w) // 2
    y = (400 - h) // 2

    draw.text((x, y), name, fill=(0, 0, 0), font=font)
    img.save(path)
    print(f"Created: {path}")

def main():
    base = "ImagesAttendance"
    os.makedirs(base, exist_ok=True)

    classes = {
        "Class_10A": ["kunal", "alice", "bob"],
        "Class_10B": ["charlie", "diana"],
        "Class_11A": ["eve", "frank"]
    }

    for cls, students in classes.items():
        cls_path = os.path.join(base, cls)
        os.makedirs(cls_path, exist_ok=True)
        for s in students:
            create_dummy_face(s, os.path.join(cls_path, f"{s}.jpg"))

    print("\nDemo setup complete!")
    print("Folder created: ImagesAttendance/")
    print("   Class_10A/kunal.jpg, alice.jpg, bob.jpg")
    print("   Class_10B/charlie.jpg, diana.jpg")
    print("   Class_11A/eve.jpg, frank.jpg")
    print("\nNow run:")
    print("   python dashboard.py")
    print("   Login: admin / admin123")

if __name__ == "__main__":
    main()