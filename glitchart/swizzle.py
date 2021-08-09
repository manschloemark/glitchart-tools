""" swizzle - take the channels from an image and rearrange them. """
# Copyright (c) 2021 Mark Schloeman

from PIL import Image

def swizzle(source, swaps=None, coords=None):
    """Take an image and rearrange the channels.

    :param source: PIL image.
    :param swaps: a string with the letters "RGB" in any order.
    :returns: a PIL image.
    """
    channel_map = {"R": 0, "G": 1, "B": 2}
    if isinstance(source, str):
        source = Image.open(source)
    glitch = source.copy()
    if coords:
        rgb = glitch.crop(coords).split()
    else:
        rgb = source.split()
    bands = [rgb[channel_map.get(c, 0)] for c in swaps]
    result = Image.merge("RGB", tuple(bands))
    if coords:
        glitch.paste(result, coords)
    return glitch

# Testing
def main():
    swizzle("/home/mark/data/pictures/glitch/input/banquet.jpg", "BRG", (100, 100, 200, 200)).show()

if __name__ == "__main__":
    main()
