import os
__author__ = 'guglielmo'

def zipdir(path_to_zip, zip, root_path):
    """
    Add all files under path, recursively, to the zip file.
    """
    cwd = os.getcwd()
    os.chdir(root_path)
    for root, dirs, files in os.walk(path_to_zip):
        for file in files:
            zip.write(os.path.join(root, file))
    os.chdir(cwd)
