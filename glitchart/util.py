""" util - misc functions for the glitch art tools. """
# Copyright (c) 2021 Mark Schloeman

import os
import pathlib
import random
import configparser


def get_default_image_path():
    """ Returns a path to a default picture directory. 
    First tries to see if the user has a directory set in a config file.
    If not, uses os to get the default Pictures directory.

    :returns: a string with an absolute filepath.
    """
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), "config.ini")) # NOTE: is using the __file__ reliable enough?
    image_path = config.get("default", "image_path", fallback=None) # The path from config is assumed to be the path intended for glitch art.
    # NOTE: I want glitchart to all be contained in one place by default, so add stuff to make a glitch directory.
    if image_path is None:
        image_path = os.path.join(os.path.expanduser("~"), "Pictures")
        if not os.path.exists(image_path):
            image_path = os.path.join(os.path.expanduser("~"), "pictures")
    return image_path

# NOTE: I'm only using pathlib as a quick fix but I'd like to learn more about it and see if I could replace os
# TODO: learn more about pathlib vs os
def setup_image_path(base_dir):
    """ Creates a glitch/input, glitch/output, and glitch/temp nested inside of base_dir """
    pathlib.Path(os.path.join(base_dir, "glitch")).mkdir(parents=True, exist_ok=True)
    pathlib.Path(os.path.join(base_dir, "glitch", "input")).mkdir(parents=True, exist_ok=True)
    pathlib.Path(os.path.join(base_dir, "glitch", "output")).mkdir(parents=True, exist_ok=True)
    pathlib.Path(os.path.join(base_dir, "glitch", "temp")).mkdir(parents=True, exist_ok=True)

def cli_prompt_image(directory=None):
    """ Searches a directory for images that can be used with these tools.
    Prints a list of filenames to stdout and expects user input.
    If the input is not an integer this function will throw an exception.

    :param directory: string for an absolute directory path. If left blank it will try to find a suitable default.
    :returns:         a string filename.
    """

    # NOTE: this would not work for anybody but myself. My 'default glitchart directory' already has an input 'input' directory.
    #       other people would not. I'll have to rethink this.
    if directory is None:
        directory = os.path.join(get_default_image_path(), "input")
    files = [filename for filename in os.listdir(directory) if filename.endswith((".jpg", ".png", ".bmp"))]
    for i, f in enumerate(files):
        print(f'{i:<2}...{f}...{round(os.stat(os.path.join(directory, f)).st_size / 1024, 2):.<6} kb')
    img_index = int(input("Enter image number: "))
    return os.path.join(directory, files[img_index])


def make_temp_file(img, directory=None):
    """ Saves a Pillow Image object with a temporary name in the given directory.
    The image name will be of the form "temp" + [12 random characters A-G, 0-9].
    NOTE: this currently only saves images to jpg files. I should update that to work with other filetypes.

    :param img: PIL.Image object.
    :param directory: string for an absolute directory path. If left blank it will try to find a suitable default.
    :returns: a string for the absolute filepath of the temp image.
    """

    # NOTE: this would not work for anybody but myself. My 'default glitchart directory' already has an input 'input' directory.
    #       other people would not. I'll have to rethink this.
    if directory is None:
        directory = os.path.join(get_default_image_path(), "temp")
    temp_name = "temp" + "".join(random.choice("ABCDEFG1234567890") for _ in range(12)) + ".jpg"
    temp_file = os.path.join(directory, temp_name)
    img.save(temp_file)
    img.filename = temp_file
    return temp_file


# NOTE : this function has some security issues.
def myshow(img, viewer="gwenview", temp_directory=None):
    """ This function allows you to open PIL Images in any application you want on Linux.
    For whatever reason Pillow's implementation does not let you use anything excepty for imagemagick.

    Warning: this function is pretty insecure so I really don't recommned using it. I just use it for personal use when playing around.
    This function is also kinda dumb because it doesn't really work properly. It's supposed to delete the temp file after you close the viewer
    but if you terminate the Python script before closing the viewer it will not delete the file.
    So, again, use at your own risk lol.
    """
    if temp_directory is None:
        temp_directory = os.path.join(get_default_image_path(), "temp")
    temp_file = make_temp_file(img, temp_directory)
    command = f'({viewer} {temp_file}; rm -f {temp_file}) &'
    os.system(command)


# Testing
def main():
    from PIL import Image
    default_dir = get_default_image_path()
    print(default_dir)
    img_file = cli_prompt_image() # use default path
    print(img_file)
    img = Image.open(img_file)
    myshow(img)
    #make_temp_file(img) # use default path



if __name__ == "__main__":
    main()
