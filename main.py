from pathlib import Path
import cv2

def main():
    image_path = Path("data/raw_receipts/IMG_4241.jpg")

    image = cv2.imread(str(image_path))

    if image is None:
        print ("Cannot read image!")
        return;

    print("Image loaded succesfully!")


    print(type(image))
    print(image.dtype)


if __name__ == "__main__":
    main()