""" pixelstats - functions that take return metrics meant to be used for sorting pixels. """
# Copyright (c) 2021 Mark Schloeman

from colorsys import rgb_to_hsv
def brightness_fast(pixel):
    """
    Perceived brightness estimation formula.
    Input should be a tuple with 3 ints (red, green, blue)
    """
    return ((pixel[0] + pixel[0] + pixel[1] + pixel[1] + pixel[1] + pixel[2]) / 6) / 255


def red(pixel):
    return pixel[0]


def green(pixel):
    return pixel[1]


def blue(pixel):
    return pixel[2]


def hue(pixel):
    return rgb_to_hsv(*pixel)[0]


def saturation(pixel):
    return rgb_to_hsv(*pixel)[1]


def value(pixel):
    return rgb_to_hsv(*pixel)[2]


key_functions = {
    "Brightness (fast)": brightness_fast,
    "Red": red, "Green": green, "Blue": blue,
    "Hue": hue, "Saturation": saturation, "Value": value}

