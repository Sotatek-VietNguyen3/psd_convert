import os
from img_processor import process_folder
from gdrive_processor import authenticate_and_download_zip, upload_folder

base_dir = os.path.dirname(__file__)
source_dir = os.path.join(base_dir, 'source')
target_dir = os.path.join(base_dir, 'target')
temp_dir = os.path.join(base_dir, 'temp')

if not os.path.exists(target_dir):
    os.makedirs(target_dir)


# https://drive.google.com/file/d/1Oh2vhnnh2Rr3NDvEVTmLNaR4x_BApwOJ/view?usp=drive_link
# https://drive.google.com/file/d/1wGl_KP1WmIWOSR1bpJAM7gd-KgMMS8Ur/view?usp=drive_link
# https://drive.google.com/file/d/1q1G1UcHKRy745XT5Uppf2oi4AwVCdlEy/view?usp=drive_link
def main():
    print('Downloading')
    unzip_folder = authenticate_and_download_zip(source_dir, '1q1G1UcHKRy745XT5Uppf2oi4AwVCdlEy')

    print('Uploading')
    upload_folder_dir = os.path.join(target_dir, os.path.basename(unzip_folder))
    if not os.path.exists(upload_folder_dir):
        os.makedirs(upload_folder_dir)

    # Process all files in the source directory
    # process_folder(unzip_folder, upload_folder_dir)
    process_folder(unzip_folder, upload_folder_dir)

    # upload_folder(upload_folder_dir)


if __name__ == "__main__":
    main()
    import sys

    sys.exit()
