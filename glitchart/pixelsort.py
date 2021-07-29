""" pixelsort - This module contains functions for pixelsorting. """
# Copyright (c) 2021 Mark Schloeman

import os
import sys
from colorsys import rgb_to_hsv

from PIL import Image

from groupby import *
from pixelstats import *
from util import *

# Functions used to modify pixels
# NOTE : I'm not sure this belongs here but I don't really have a better place for it.
def brighten(pixel, modifiers):
    """ Multiply a pixel by given value(s). Works with tuples of pixels or single colors from a pixel.

    :param pixel: a tuple representing an RGB pixel or a int.
    :param modifiers: a tuple containing a value for each color in pixel or an int, if pixel is an int.
    :returns: a modified pixel value.
    """

    if isinstance(pixel, int):
        return pixel * modifiers
    return tuple([min(255, color * modifier) for color, modifier in zip(pixel, modifiers)])


# These dicts are primarily useful in the GUI, they assign strings to functions from groupby.py
# NOTE : should I use these or should I use the ones from the source modules?
# NOTE : commented these out because I have dicts for these in groupby.py
#grouping_functions = {
#        "Linear":  linear,
#        "Rows":    rows,
#        "Columns": columns,
#}
#sort_functions = {
#    "Linear": linear_sort,
#    "Shutters": shutters,
#    "Tracers": tracers,
#    "Wobbly Tracers": tracers_wobbly,
#}


def sort_pixels(pixels, size, group_func, sort_func, key_func, reverse=False, color_mods=(1, 1, 1), **kwargs):
    """ Lowest level function that is used to perform a pixel sort.
    The reason this is separate from the sort_image function is so it can sort bands as well. I think it'll keep things more organized.
    Note: when sorting bands the key_func should really just be a function or lambda that immediately returns the value passed to it.

    :param pixels:     a 1 dimensional list of pixels from a Pillow Image or Band object
    :param size:       a list containing width and height of the overall image
    :param group_func: a function or generator
    :param sort_func:  a function or generator
    :param key_func:   a function that is used as the key in python's sorted() function
    :param reverse:    boolean used to reverse the sort order
    :param color_mods: tuple of numbers used to modify sorted pixels
    :param kwargs:     any keyword arguments that will be passed to the sort_func

    :returns: a list of sorted pixels.
    """

    sorted_pixels = []
    for pixel_list in group_func(pixels, size):
        for sorting_group, sort_flag in sort_func(pixel_list, **kwargs):
            if sort_flag:
                sorted_pixels += [brighten(pixel, color_mods)
                                 for pixel in sorted(sorting_group,
                                                     key=key_func,
                                                     reverse=reverse)]
            else:
                sorted_pixels += sorting_group
    if group_func is columns:
        sorted_pixels = transpose_list(sorted_pixels, size[1])
    return sorted_pixels

def sort_image(src, grouping_function, sort_function, key_function, reverse=False, color_mods=(1, 1, 1), **kwargs):
    """ Function that sorts the pixels in an image.

    :param src:        a Pillow Image object to be sorted OR a string indicating filepath to image.
    :param group_func: a shaping function or generator that OR a string that maps to a generator.
    :param sort_func:  a sorting function or generator OR a string that maps to a generator.
    :param key_func:   a function that is used as the key in python's sorted() function for pixels (tuples).
    :param reverse:    boolean used to reverse the sort order.
    :param color_mods: tuple of numbers used to modify sorted pixels.
    :param kwargs:     any keyword arguments that will be passed to the sort_func.

    :returns:          a Pillow Image with the sorted pixels.
    """

    if isinstance(src, str):
        src = Image.open(src)
    if isinstance(grouping_function, str):
        grouping_function = group_generators[grouping_function]
    if isinstance(sort_function, str):
        sort_function = sort_generators.get(sort_function, linear_sort)
    if isinstance(key_function, str):
        key_function = key_functions[key_function]
    glitch = src.copy()
    pixels = sort_pixels(
                        list(glitch.getdata()),
                        src.size,
                        grouping_function,
                        sort_function,
                        key_function,
                        reverse,
                        color_mods,
                        **kwargs
                        )

    glitch.putdata(pixels)
    return glitch


# This function is annoying to use, I'm only keeping it in case I want to
# use it in code.
# The GUI for bandsorting will not use this, it'll just use sort_pixels
def sort_bands(src, group_tuple, sort_tuple, reverse=(False, False, False), pixel_mods=(1, 1, 1), **kwargs):
    """ Function that sorts the pixels of each channel in an RGB image.
    NOTE: this function is probably not going to be used.

    :param src:         a Pillow Image object to be sorted OR a string indicating filepath to image.
    :param group_tuple: a tuple of three shaping functions or generators for the RGB channels.
    :param sort_tuple:  a tuple of three sorting functions or generators for the RGB channels.
    :param reverse:     a tuple of booleans used to reverse the sort order of each RGB channel.
    :param color_mods:  tuple of numbers used to modify sorted pixels.
    :param kwargs:      not actually used.

    :returns:          a Pillow Image with sorted pixels.
    """

    if isinstance(src, str):
        src = Image.open(src)
    sorted_bands = []
    for index, band in enumerate(src.split()):
        pixels = sort_pixels(
                        list(band.getdata()),
                        src.size,
                        group_tuple[index],
                        sort_tuple[index],
                        lambda x: x,
                        reverse[index],
                        pixel_mods[index]
                        )
        band.putdata(pixels)
        sorted_bands.append(band)
    glitch = Image.merge('RGB', tuple(sorted_bands))
    return glitch

def main():
    #glitch = sort_image(
    #    "/home/mark/data/pictures/glitch/input/banquet.jpg",
    #    "Linear",
    #    "Linear",
    #    "Brightness (fast)",
    #    False,
    #    color_mods=(1.5, 1.5, 2.0)
    #)
    #myshow(glitch)
    glitch = sort_bands(
            "/home/mark/data/pictures/glitch/input/banquet.jpg",
            (linear, rows, columns),
            (shutters, linear_sort, tracers),
            (False, False, False),
     )
    glitch.show()


if __name__ == "__main__":
    main()

