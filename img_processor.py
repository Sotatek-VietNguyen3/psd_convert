import os
import subprocess
from pathlib import Path
from psd_tools import PSDImage
from PIL import Image

base_dir = os.path.dirname(__file__)
source_dir = os.path.join(base_dir, 'source')
target_dir = os.path.join(base_dir, 'target')


class ImageProcessor:
    temp_dir = os.path.join(base_dir, 'temp')
    temp_img = os.path.join(temp_dir, 'img.png')
    type_file = [
        'image/vnd.adobe.photoshop',
        'image/jpeg',
        'image/png',
        'image/jpg',
    ]

    def __init__(self, input_file, output_file, height=None, width=760):
        self.input_file = input_file
        self.output_file = output_file
        self.height = height
        self.width = width
        self.is_psd = True

    def resize_image(self):
        try:
            image = self._open_image()
        except Exception as e:
            print(e)
            return

        original_width, original_height = image.size
        if self.width and not self.height:
            self.height = int((self.width / original_width) * original_height)
        elif self.height and not self.width:
            self.width = int((self.height / original_height) * original_width)
        elif not self.width and not self.height:
            self.width, self.height = original_width, original_height

        resized_image = image.resize((self.width, self.height), Image.Resampling.LANCZOS)
        resized_image.save(self.temp_img)
        converted = self._convert_image_to_psd()
        if converted:
            self._remove_psd_source_file()

    def _open_image(self):
        type_file = self._get_input_file_type()
        if type_file not in self.type_file:
            raise Exception("Invalid file type")

        if type_file == self.type_file[0]:
            image = PSDImage.open(self.input_file)
            composite_image = image.composite()
            return composite_image

        else:
            self.is_psd = False
            image = Image.open(self.input_file)
            return image

    def _convert_image_to_psd(self):
        _cmd = f"magick \"{self.temp_img}\" \"{self.output_file}\""

        return self._execute_cmd(_cmd)

    def _get_input_file_type(self):
        _cmd = f"file --mime-type -b \"{self.input_file}\""
        result = self._execute_cmd(_cmd)
        if not result:
            return None
        return result.stdout.lower().strip()

    def _remove_psd_source_file(self):
        _cmd = f"rm \"{self.input_file}\""
        if self.temp_img:
            _cmd += f"  \"{self.temp_img}\""
        self._execute_cmd(_cmd)

    def _execute_cmd(self, cmd):
        print(cmd)
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error executing command: {cmd}")
            print(result.stderr)
            return None
        return result


def process_folder(folder_path, folder_result):
    for root, _, files in os.walk(folder_path):
        # Calculate the relative path to maintain the same folder structure
        relative_path = Path(root).relative_to(folder_path)
        target_folder = Path(folder_result) / relative_path

        # Create the target folder if it doesn't exist
        target_folder.mkdir(parents=True, exist_ok=True)

        for file in files:

            input_file = Path(root) / file
            output_file = Path(target_folder) / (file.rsplit('.', 1)[0] + ".psd")

            # Initialize the processor
            processor = ImageProcessor(input_file=input_file, output_file=output_file)
            processor.resize_image()


process_folder(source_dir, target_dir)
