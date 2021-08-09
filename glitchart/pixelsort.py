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
# NOTE : I'm not sure this belongs here but right now I don't have a better place for it.
def brighten(pixel, modifiers):
    """ Multiply a pixel by given value(s). Works with tuples of pixels or single colors from a pixel.

    :param pixel: a tuple representing an RGB pixel or a int.
    :param modifiers: a tuple containing a value for each color in pixel or an int, if pixel is an int.
    :returns: a modified pixel value.
    """

    if isinstance(pixel, int):
        return int(pixel * modifiers)
    return tuple([min(255, int(color * modifier)) for color, modifier in zip(pixel, modifiers)])


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
    :param kwargs:     any keyword arguments that will be passed to the sort_func and/or the group_func.

    :returns: a list of sorted pixels.
    """

    sorted_pixels = []
    for pixel_list in group_func(pixels, size, **kwargs):
        for sorting_group, sort_flag in sort_func(pixel_list, **kwargs):
            if sort_flag:
                sorted_pixels += [brighten(pixel, color_mods)
                                 for pixel in sorted(sorting_group,
                                                     key=key_func,
                                                     reverse=reverse)]
            else:
                sorted_pixels += sorting_group
    transpose_function = group_transpose_generators.get(group_func, None)
    if transpose_function is not None:
        sorted_pixels = group_transpose_generators[group_func](sorted_pixels, size, **kwargs)
    return sorted_pixels

def sort_image(src, grouping_function, sort_function, key_function, reverse=False, color_mods=(1, 1, 1), coords=None, **kwargs):
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
    result = src.copy()
    if coords:
        glitch = src.crop(coords)
    else:
        glitch = result
    pixels = sort_pixels(
                        list(glitch.getdata()),
                        glitch.size,
                        grouping_function,
                        sort_function,
                        key_function,
                        reverse,
                        color_mods,
                        **kwargs
                        )

    glitch.putdata(pixels)
    if coords:
        result.paste(glitch, coords)
    return result


def sort_part(src, coords, grouping_function, sort_function, key_function, reverse=False, color_mods=(1, 1, 1), **kwargs):
    """ Function that crops a part of an image, sorts it, and pastes it back onto the original.

    :param src:        a Pillow Image object to be sorted OR a string indicating filepath to image.
    :param coords:     a tuple containing coordinates (left, upper, right, lower) to make PIL.Image.crop()
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
    result = src.copy()
    glitch = src.crop(coords)
    pixels = sort_pixels(
                        list(glitch.getdata()),
                        glitch.size,
                        grouping_function,
                        sort_function,
                        key_function,
                        reverse,
                        color_mods,
                        **kwargs
                        )

    glitch.putdata(pixels)
    result.paste(glitch, coords)
    return result


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
    glitch = sort_image(
        "/home/mark/data/pictures/glitch/input/hasui.jpg",
        "Diagonals",
        "Linear",
        "Blue",
        False,
        color_mods=(1, 1, 1),
        coords=(200, 200, 400, 400)
    )
    myshow(glitch)
    glitch2 = sort_image(
        "/home/mark/data/pictures/glitch/input/hasui.jpg",
        "Diagonals",
        "Linear",
        "Blue",
        False,
        color_mods=(1, 1, 1),
    )
    myshow(glitch2)
    #myshow(glitch)
    #glitch = sort_bands(
    #        "/home/mark/data/pictures/glitch/input/banquet.jpg",
    #        (linear, rows, columns),
    #        (shutters, linear_sort, tracers),
    #        (False, False, False),
    #)


if __name__ == "__main__":
    main()

