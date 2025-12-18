import os

def get_filename_and_extension(file_path: str):
    base_name = os.path.basename(file_path)
    file_name, extension = os.path.splitext(base_name)
    return file_name, extension