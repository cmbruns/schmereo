import os
import sys

from PIL import Image


def main():
    file_name = sys.argv[1]
    image = Image.open(file_name)
    w, h = image.size
    base, extension = os.path.splitext(file_name)
    #
    left_name = f"{base}_L.jpg"
    left = image.crop((0, 0, w/2, h)).convert('RGB')
    left.save(left_name, 'JPEG', quality=90)
    #
    right_name = f"{base}_R.jpg"
    right = image.crop((w/2, 0, w, h)).convert('RGB')
    right.save(right_name, 'JPEG', quality=90)


if __name__ == "__main__":
    main()
