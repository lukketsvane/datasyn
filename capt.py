import os
import time
from PIL import Image

# Folder
folder = "frames"

# Create the frames folder if it doesn't exist
frames_dir = os.path.join(os.getcwd(), folder)
os.makedirs(frames_dir, exist_ok=True)

def process_image(image_path):
    try:
        pil_img = Image.open(image_path)

        # Resize the image
        max_size = 250
        ratio = max_size / max(pil_img.size)
        new_size = tuple([int(x*ratio) for x in pil_img.size])
        resized_img = pil_img.resize(new_size, Image.LANCZOS)

        # Save the resized image
        resized_img.save(image_path)
        print(f"Processed and saved: {image_path}")
    except IOError as e:
        print(f"Error processing image: {e}")

def main():
    last_processed_time = 0
    while True:
        for filename in os.listdir(frames_dir):
            if filename.endswith(".jpg") or filename.endswith(".png"):
                image_path = os.path.join(frames_dir, filename)
                file_modified_time = os.path.getmtime(image_path)
                
                if file_modified_time > last_processed_time:
                    process_image(image_path)
                    last_processed_time = file_modified_time

        # Wait for 2 seconds before checking for new images
        time.sleep(2)

if __name__ == "__main__":
    main()
