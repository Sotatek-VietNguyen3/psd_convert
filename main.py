import os
from pathlib import Path

from gdrive_processor import GDriveProcessor
from img_processor import ImageProcessor

base_dir = os.path.dirname(__file__)
source_dir = os.path.join(base_dir, 'source')
target_dir = os.path.join(base_dir, 'target')


def main():
    print('Downloading')
    processor = GDriveProcessor(download_folder_id=download_folder_id, upload_folder_id=upload_folder_id)
    processor.download_folder()

    for root, _, files in os.walk(source_dir):
        # Calculate the relative path to maintain the same folder structure
        relative_path = Path(root).relative_to(source_dir)
        target_folder = Path(target_dir) / relative_path

        # Create the target folder if it doesn't exist
        target_folder.mkdir(parents=True, exist_ok=True)

        for file in files:

            input_file = Path(root) / file
            output_file = Path(target_folder) / (file.rsplit('.', 1)[0] + ".psd")

            # Initialize the processor
            processor = ImageProcessor(input_file=input_file, output_file=output_file)
            processor.resize_image()

    processor.upload_folder(target_dir)


if __name__ == "__main__":
    download_folder_id = input("Enter download folder id: ")
    upload_folder_id = input("Enter upload folder id: ")
    main()

    import sys

    sys.exit()
