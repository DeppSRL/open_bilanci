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


def zipdir_prefix(zipfile, rootpath, folder, prefix):
    """
    Add all files under path, recursively, to the zip file.
    Allows to have a folder prefix in the generated zip
    """

    cwd = os.getcwd()
    os.chdir(rootpath)
    for root, dirs, files in os.walk(os.path.join(".", folder)):
        for f in files:
            zipfile.write(os.path.join(root, f), arcname=prefix+"/"+os.path.join(root, f))
    os.chdir(cwd)