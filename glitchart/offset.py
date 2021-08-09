""" offset - Rotate or offset lines in an image """

import math

import pixelsort
from PIL import Image
import groupby

# Offset Helper Functions
# It feels wasteful to have functions that just return numbers but it keeps the code simpler... I think
def static_number(line_number, offset, **kwargs):
    return offset

def line_number(line_number, **kwargs):
    return line_number

def sine(line_number, height, inv_wavelength, **kwargs):
    return int(height * math.sin(line_number * inv_wavelength * math.pi / 2))

def cosine(line_number, height, inv_wavelength, **kwargs):
    return int(height * math.cos(line_number * inv_wavelength * math.pi / 2))


def offset(source, line_generator, offset_function, coords=None, **kwargs):
    """ Run an image through a line generator (from groupby.py) and rotate the lines

    :param source: a string containing path to an image or a PIL Image object
    :param line_generator: a generator from groupby.py used to delineate an image (linear, rows, columns, etc.)
    :param offset_function: a function that takes two ints and is used to determine the offset.
    :returns: a PIL Image
    """
    if isinstance(source, str):
        source = Image.open(source)
    if isinstance(line_generator, str):
        line_generator = groupby.group_generators.get(line_generator)
    if isinstance(offset_function, str):
        offset_function = offset_functions.get(offset_function)
    result = source.copy()
    if coords:
        glitch = result.crop(coords)
        pixels = list(glitch.getdata())
    else:
        glitch = result
        pixels = list(glitch.getdata())
    result_pixels = []
    # Trying start and end to wave offsets don't wrap around the image
    for line_number, line in enumerate(line_generator(pixels, glitch.size)):
        offset = offset_function(line_number, **kwargs)
        result_pixels += line[offset :] + line[: offset]

    transposer = groupby.group_transpose_generators.get(line_generator)
    if transposer:
        result_pixels = transposer(result_pixels, glitch.size, **kwargs)

    glitch.putdata(result_pixels)
    if coords:
        result.paste(glitch, coords)
    return result

offset_functions = {"Line Number": line_number, "Static": static_number, "Sine": sine, "Cosine": cosine}


def main():
    src = Image.open("/home/mark/data/pictures/glitch/input/banquet.jpg")
    offset(src, groupby.rows, sine, height=48, inv_wavelength=math.pi / 200, coords=(100, 100, 300, 300)).show()
    src2 = Image.open("/home/mark/data/pictures/glitch/input/banquet.jpg")
    offset(src2, groupby.rows, static_number, offset=69).show()
    src3 = Image.open("/home/mark/data/pictures/glitch/input/banquet.jpg")
    offset(src3, groupby.columns, cosine, height=48, inv_wavelength=math.pi / 200).show()


if __name__ == "__main__":
    main()
