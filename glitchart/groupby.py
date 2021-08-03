""" groupby - this module contains functions and generators for delineating image pixels before sorting. """
# Copyright (c) 2021 Mark Schloeman

import random

from pixelstats import *

# Shape delineation - yield / return pixels from the list based on the shape of the image
####################################################
def linear(source_pixels, *args, **kwargs):
    """ Keeps a list of pixels as a 1 dimensional array.  This function is only necessary to keep the api consistent.
    
    :param: source_pixels: a list of pixels.
    :returns: a list containing a list of pixels.
    """

    return [source_pixels]

def rows(source_pixels, source_size, **kwargs):
    """ Generator that yields rows from a list of pixels. 

    :param source_pixels: a list of pixels.
    :param source_size:   an interable containing the image's (width, height).
    :returns: rows as lists of pixels.
    """

    for x in range(0, len(source_pixels), source_size[0]):
        yield source_pixels[x : x + source_size[0]]



# NOTE : this messes up the order of the pixels.
#        you need to transpose the list after using this
def columns(source_pixels, source_size, **kwargs):
    """ Generator that yields columns from a list of pixels. 
    NOTE : in order to use this properly you must use the function transpose_list afterwards because this will mess up the shape of the image.

    :param source_pixels: a list of pixels.
    :param source_size:   an interable containing the image's (width, height).
    :returns: columns as lists of pixels.
    """

    for x in range(0, source_size[0]):
        yield source_pixels[x : : source_size[0]]

def columns_fix(source_list, source_size, **kwargs):
    """ Transpose a list so its columns are rows.

    :param source_list: a list of pixels.
    :param pitch: PIL Image size attribute, a tuple with two ints.
    :returns: a list of pixels.
    """

    result = []
    for y in range(0, source_size[1]):
        result += source_list[y :: source_size[1]]
    return result


def diagonals(source_pixels, source_size, flip_slope=False, **kwargs):
    """ Generator that yields diagonal lines from an image. Starts from one corner to the opposite.

    Currently it starts at the bottom left of the image and travels along the left and top sides.
    It yields diagonal lines going down and to the right, stopping at the opposite border.
    TODO : add options to start at any corner.

    :param source_pixels: a list of pixels.
    :param source_size:   an interable containing the image's (width, height).
    :param corner:        a flag that determines which direction the lines run
                          True = backslash False = forwardslash
    :returns: columns as lists of pixels.
    """
    pitch, height = source_size
    if flip_slope: # Lines look like this: /
        start_x = 0
        start_y = 0
        end_y = height - 1
        x_inc = 1
        y_inc = -1
        y_border = -1
    else: # Lines look like this: \
        start_x = 0
        start_y = height - 1
        end_y = 0
        x_inc = 1
        y_inc = 1
        y_border = height

    for i in range(source_size[0] + source_size[1] - 1):
        line = []
        x = start_x
        y = start_y
        while y != y_border and x < pitch:
            line.append(source_pixels[x + (y * pitch)])
            x += x_inc
            y += y_inc
        if start_y != end_y:
            start_y -= y_inc
        else:
            start_x += x_inc
        yield line

def diagonals_fix(source_pixels, source_size, flip_slope=False, **kwargs):
    pitch, height = source_size
    if flip_slope:
        x = start_x = 0
        y = start_y = 0
        end_y = height - 1
        y_border = -1
        x_inc = 1
        y_inc = -1
    else:
        x = start_x = 0
        y = start_y = height - 1
        end_y = 0
        y_border = height
        x_inc = 1
        y_inc = 1
    # This is probably pretty slow but it's the easiest way I can think to do this rn
    result = [0] * (pitch * height)
    for pixel in source_pixels:
        result[x + (y * pitch)] = pixel
        x += x_inc
        y += y_inc
        if x == pitch or y == y_border:
            if start_y != end_y:
                start_y -= y_inc
            else:
                start_x += x_inc
            x = start_x
            y = start_y
    return result


def wrapping_diagonals(source_pixels, source_size, **kwargs):
    """ Generator that yields diagonals from a list of pixels.

    This generator starts at the top left of the image (index 0 of the array) and yields lines going down and to
    the right. This one wraps around the image when it reaches a border.

    :param source_pixels: a list of pixels.
    :param source_size:   an interable containing the image's (width, height).
    :returns: columns as lists of pixels.
    """
    # This function is making me realize that using indices to access the array would be convenient.
    for x in range(source_size[0]):
        x_index = x
        line = []
        for y in range(source_size[1]):
            if x_index >= source_size[0]:
                x_index = 0
            line.append(source_pixels[x_index + (y * source_size[0])])
            x_index += 1
        yield line

def wrapping_diagonals_fix(source_pixels, source_size, **kwargs):
    result = []
    index = 0
    row_length = 0
    for _ in range(len(source_pixels)):
            result.append(source_pixels[index])
            row_length += 1
            if row_length == source_size[0]:
                index += 1
                row_length = 0
            else:
                index += source_size[1]
            if index > len(source_pixels):
                index %= len(source_pixels)
    return result


# TODO finish implementing this one and it's matching fix function
def linear_slope(source_pixels, source_size, slope=(1, 1), **kwargs):
    """ Generator that yields lines with a linear slope from a list of pixels

    The lines yielded start from one edge of the image and stop at the opposite edge following the given slope.
    If slope = (1, 2) that means it moves right one every 2 rows.
    A negative value in the slope means it starts at the opposite end of the image.

    :param source_pixels: a list of pixels.
    :param source_size:   an interable containing the image's (width, height).
    :param slope: a tuple containing the rise and run, the change in x and y.
    :returns: columns as lists of pixels.
    """
    # Defaults
    pitch = source_size[0]
    start_x = 0
    end_x = source_size[0]
    column_iterator = range(source_size[0])
    start_y = 0
    end_y = source_size[1] * source_size[0]
    row_iterator = range(0, source_size[0] * source_size[1], pitch)

    dx, dy = slope # NOTE not sure on whether the tuple should be (dx, dy) or (dy, dx).
    if dx < 0:
        start_x = source_size[0] - 1
        end_x = -1
        column_iterator = range(start_x, -1, -1)
    if dy < 0:
        start_y = (source_size[1] - 1) * pitch
        end_y = -1
        row_iterator = range(start_y, -1, -1 * pitch)

    if abs(dy) < abs(dx):
        outer_iterator = row_iterator
        inner_iterator = column_iterator
        start_i = start_y
        end_i = end_y
        start_j = start_x
        end_j = end_x
        di = dy
        di_increment = dy * pitch
        dj = dx
    else:
        outer_iterator = column_iterator
        inner_iterator = row_iterator
        start_i = start_x
        end_i = end_x
        start_j = start_y
        end_j = end_y
        di = dx
        di_increment = dx
        dj = dy

    print(start_i)
    print(pitch)
    print(end_i)
    for i in outer_iterator:
        i_index = i
        line = []
        di_remaining = abs(di)
        dj_remaining = abs(dj)
        for j in inner_iterator:
            if i_index == end_i:
                i_index = start_i
            line.append(source_pixels[i_index + j])
            if di_remaining > 0:
                i_index += di_increment
                di_remaining -= 1
            dj_remaining -= 1
            if dj_remaining == 0:
                di_remaining = di
                dj_remaining = dj
        yield line

def linear_slope_fix(source_pixels, source_size, slope=(1, 1), **kwargs):
    """ Helper function that rearranges a list after it has gone through linear_slope. """
    # NOTE : do this while I'm still working on the proper slope fix.
    return wrapping_diagonals_fix(source_pixels, source_size)
    # Defaults
    pitch = source_size[0]
    start_x = 0
    end_x = source_size[0]
    column_iterator = range(source_size[0])
    start_y = 0
    end_y = source_size[1] * source_size[0]
    row_iterator = range(0, source_size[0] * source_size[1], pitch)

    dx, dy = slope # NOTE not sure on whether the tuple should be (dx, dy) or (dy, dx).
    if dx < 0:
        start_x = source_size[0] - 1
        end_x = -1
        column_iterator = range(start_x, -1, -1)
    if dy < 0:
        start_y = (source_size[1] - 1) * pitch
        end_y = -1
        row_iterator = range(start_y, -1, -1 * pitch)
    # The index of source_pixels that must be mapped to index 0 of result 
    # depends on the absolute values and signs of the slope.
    # If the slope is (+ / +) then index 0 is at index 0 of list 0
    # If the slope is (+ / -) then index 0 is at index 0 of the last list.
    # If the slope is (- / +) then index 0 depends on the magnitude of the slope.
    # If the slope is (- / -) then index 0 depends on the magnitude of the slope.
    if abs(dy) < abs(dx):
        start_i = start_y
        end_i = end_y
        start_j = start_x
        end_j = end_x
        di = dy
        dj = dx
    else:
        start_i = start_x
        end_i = end_x
        start_j = start_y
        end_j = end_y
        di = dx
        dj = dy
    d_inc = 1
    offset_inc = 1
    if di < 0:
        d_inc = -1
        columns_reversed = True
        start_x = source_size[0] - 1
        end_x = -1
        column_iterator = range(start_x, -1, -1)
    if dj < 0:
        offset_inc = -1
        rows_reversed = True
        start_y = (source_size[1] - 1) * pitch
        end_y = -1
        row_iterator = range(start_y, -1, -1 * pitch)

    d_len = source_size[0]
    diag_width = 1 + dx * (source_size[1] - 1 / dy)

    start_col = start_x
    start_row = start_y
    if start_row > 0:
        start_offset_line_index = start_col - diag_width
    start_offset_index_of_line = start_row
    d_num = start_offset_line_index
    i_index = start_offset_index_of_line
    i_increment = 1
    wrap_index = source_size[0]
    row_len = 0
    for _ in range(len(source_pixels)):
        result.append(d_num * d_len + offset)
        if di_ctr:
            col_num += col_inc
            if col_num == wrap_index:
                i_index += i_increment

    return result

# NOTE commenting this version out because it is slightly different and I'm not sure I want it.
#      the diff b/t this and the used version is that this chooses the direction of the line
#      based on the width/dx and height/dy instead of the magnitudes of dx and dy.
#def linear_slope_fix(source_pixels, source_size, slope=None, **kwargs):
#    """ Helper function that rearranges a list after it has gone through linear_slope. """
#    # Copy all of the loop setup from linear_slope
#    # Defaults
#    pitch = source_size[0]
#    start_x = 0
#    end_x = source_size[0]
#    column_iterator = range(source_size[0])
#    start_y = 0
#    end_y = source_size[1]
#    row_iterator = range(0, source_size[0] * source_size[1], pitch)
#
#    dx, dy = slope # NOTE not sure on whether the tuple should be (dx, dy) or (dy, dx).
#    if dx < 0:
#        start_x = source_size[0] - 1
#        end_x = -1
#        column_iterator = range(start_x, -1, -1)
#    if dy < 0:
#        start_y = (source_size[1] - 1) * pitch
#        end_y = -1
#        row_iterator = range(start_y, -1, -1 * pitch)
#
#    # The axis that takes fewer loops will be used as the inner loop
#    if dx:
#        x_increments = source_size[0] / dx
#    else:
#        x_increments = 0
#    if dy:
#        y_increments = source_size[1] / dy
#    else:
#        y_increments = 0
#    if abs(y_increments) < abs(x_increments):
#        outer_iterator = row_iterator
#        inner_iterator = column_iterator
#        start_i = start_y
#        end_i = end_y
#        start_j = start_x
#        end_j = end_x
#        di = dy * pitch
#        dj = dx
#    else:
#        outer_iterator = column_iterator
#        inner_iterator = row_iterator
#        start_i = start_x
#        end_i = end_x
#        start_j = start_y
#        end_j = end_y
#        di = dx
#        dj = dy * pitch
#
#    for i in outer_iterator:
#        i_index = i
#        line = []
#        di_remaining = abs(di)
#        dj_remaining = abs(dj)
#        for j in inner_iterator:
#            if i_index == end_i:
#                i_index = start_i
#            line.append(source_pixels[i_index + j])
#            if di_remaining > 0:
#                i_index += di
#                di_remaining -= 1
#            dj_remaining -= 1
#            if dj_remaining == 0:
#                di_remaining = di
#                dj_remaining = dj
#        yield line
#
#
#
#def linear_slope(source_pixels, source_size, slope=None, **kwargs):
#    """ Generator that yields lines with a linear slope from a list of pixels
#
#    :param source_pixels: a list of pixels.
#    :param source_size:   an interable containing the image's (width, height).
#    :param slope: a tuple containing the rise and run, the change in x and y.
#    :returns: columns as lists of pixels.
#    """
#    # Defaults
#    pitch = source_size[0]
#    start_x = 0
#    end_x = source_size[0]
#    column_iterator = range(source_size[0])
#    start_y = 0
#    end_y = source_size[1] * source_size[0]
#    row_iterator = range(0, source_size[0] * source_size[1], pitch)
#
#    dx, dy = slope # NOTE not sure on whether the tuple should be (dx, dy) or (dy, dx).
#    if dx < 0:
#        start_x = source_size[0] - 1
#        end_x = -1
#        column_iterator = range(start_x, -1, -1)
#    if dy < 0:
#        start_y = (source_size[1] - 1) * pitch
#        end_y = -1
#        row_iterator = range(start_y, -1, -1 * pitch)
#
#    # The axis that takes fewer loops will be used as the inner loop
#    if dx:
#        x_increments = source_size[0] / dx
#    else:
#        x_increments = 0
#    if dy:
#        y_increments = source_size[1] / dy
#    else:
#        y_increments = 0
#    if abs(y_increments) > abs(x_increments):
#        outer_iterator = row_iterator
#        inner_iterator = column_iterator
#        start_i = start_y
#        end_i = end_y
#        start_j = start_x
#        end_j = end_x
#        di = dy
#        di_increment = dy * pitch
#        dj = dx
#    else:
#        outer_iterator = column_iterator
#        inner_iterator = row_iterator
#        start_i = start_x
#        end_i = end_x
#        start_j = start_y
#        end_j = end_y
#        di = dx
#        di_increment = dx
#        dj = dy
#
#    print(start_i)
#    print(pitch)
#    print(end_i)
#    for i in outer_iterator:
#        i_index = i
#        line = []
#        di_remaining = abs(di)
#        dj_remaining = abs(dj)
#        for j in inner_iterator:
#            if i_index == end_i:
#                i_index = start_i
#            line.append(source_pixels[i_index + j])
#            if di_remaining > 0:
#                i_index += di_increment
#                di_remaining -= 1
#            dj_remaining -= 1
#            if dj_remaining == 0:
#                di_remaining = di
#                dj_remaining = dj
#        yield line

# Generators / Functions that yield / return sortable tuples.
# The first item is the list of pixels
# The second is a boolean telling whether or not the list should be sorted
# NOTE : I'm still a little shaky on the (pixels, sort_flag) tuple because for most
#        of these generators they are redundant. But it's nice beacuse it makes everything work
#        with just one API

def linear_sort(source_pixels, **kwargs):
    """ Return the pixels given to be sorted.
    
    :param source_pixels: a list if pixels.
    :returns: a list containing a tuple containing the pixels and a sorting flag.
    """

    # Have to return an iterable containing the tuple so glitchart.sort_image can work with this
    # the same way it works with the others
    return [(source_pixels, True)]

def shutters(source_pixels, shutter_size=None, **kwargs):
    """ Generator that yields chunks of the image to be sorted.

    :param source_pixels: a list of pixels.
    :param shutter_size:  an integer that tells how many pixels to yield at once. If not it will be 1/10 the length of source_pixels.
    :returns: tuples containing a chunk of the source pixels and a sorting flag.
    """
    if shutter_size is None:
        shutter_size = len(source_pixels) // 10
    for index in range(0, len(source_pixels), shutter_size):
        yield (source_pixels[index : index + shutter_size], True)

def variable_shutters(source_pixels, min_size=None, max_size=None, **kwargs):
    """ Generator that yields chunks that vary between a minimum and maximum size

    :param source_pixels: a list of pixels.
    :param min_size:  an integer that determines the minimum number of pixels to yield
    :param max_size:  an integer that determines the maximum number of pixels to yield
    :returns: tuples containing a chunk of the source pixels and a sorting flag.
    """
    if min_size is None:
        min_size = len(source_pixels) // 10
    if max_size is None:
        max_size = min_size * 1.5

    left_index = 0
    while left_index < len(source_pixels):
        right_index = left_index + random.randint(min_size, max_size)
        yield (source_pixels[left_index : right_index], True)
        left_index = right_index


# Complex generators that yield list based on pixel characteristics
# NOTE : these won't work on bands
# TODO : make more parameters - tracer length, contrast function, mask
def tracers(line, tracer_length=44, border_width=2, variance_threshold=None, **kwargs):
    """ Generator attempts to identify borders between objects and return a list of pixels within the borders and then a list of pixels extending out of the border.
        Only the trail should be sorted.

        :param line: a list of pixels.
        :param tracer_length: an integer for the number of pixels to include in each tracer.
        :param border_width: how many pixels need to satisfy the border condition in a row to trigger the tracer effect.
        :param variance_threshold: a number between 0.0 and 1.0 that determines the difference in brightness required for two pixels to be considered a border.
        :returns: tuples containing a list of pixels and a sorting flag.
    """
    if isinstance(line[0], int):
        variance_metric = lambda x: x/255
    else:
        variance_metric = brightness_fast
    variance_threshold = variance_threshold or 0.25
    # TODO
    # sort_list flag is used in an attempt to avoid making a tracer on the inside of an
    # object in the image instead of trailing on the outside.
    # Though it doesn't work if the object in the image starts at index 0.
    # So this will have to be changed
    sort_list = False
    group_start = 0
    x = 0
    while x < (len(line) - border_width):
        at_border = True
        for x2 in range(x + 1, min(len(line), x + border_width)):
            if (abs(variance_metric(line[x]) - variance_metric(line[x2])) < variance_threshold):
                at_border = False
                break
        if at_border:
            if sort_list:
                yield (line[group_start : x], False)
                tracer_end = min(len(line), x + tracer_length)
                yield (line[x : tracer_end], True)
                group_start = tracer_end
                x = tracer_end
                sort_list = False
            else:
                sort_list = True
        else:
            x += 1
    yield (line[group_start :], False)


# Generators that came from mistakes
####################################
def tracers_wobbly(line, tracer_length=44, border_width=2, **kwargs):
    """
        At each pixel, check if the border_width subsequent pixels 
        have a variance greater than var_limit. If they all pass,
        the next tracer_length pixels will be sorted.
        This function came about while changing something in the tracer
        function. It makes the image all wobbly. Kind of reminds me of The Scream

        :param line: a list of pixels.
        :param tracer_length: an integer for the number of pixels to include in each tracer.
        :param border_width: how many pixels need to satisfy the border condition in a row to trigger the tracer effect.
        :returns: tuples containing a list of pixels and a sorting flag.
    """
    if isinstance(line[0], int):
        variance_metric = lambda x: x
    else:
        variance_metric = brightness_fast
    variance_threshold = 0.2
    i = 0
    while i < len(line):
        border = True
        for j in range(1, border_width + 1):
            if i + j >= len(line) or abs(variance_metric(line[i]) - variance_metric(line[j])) < variance_threshold:
                border = False
        if border:
            yield (line[i + 1 : i + tracer_length + 1], True)
            i += tracer_length + 1
        else:
            yield ([line[i]], True)
            i += 1


group_generators = {"Linear": linear, "Rows": rows, "Columns": columns, "Diagonals": diagonals, "Wrapping Diagonals": wrapping_diagonals, "Linear Slope": linear_slope}
group_transpose_generators = {columns: columns_fix, diagonals: diagonals_fix, linear_slope: linear_slope_fix, wrapping_diagonals: wrapping_diagonals_fix}
sort_generators = {"Linear": linear_sort, "Shutters": shutters, "Variable Shutters": variable_shutters, "Tracers": tracers, "Wobbly Tracers": tracers_wobbly}
