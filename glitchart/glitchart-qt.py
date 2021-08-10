""" glitchart-qt - Qt GUI for glitch art tools. Uses PySide6."""
# Copyright (c) 2021 Mark Schloeman

import sys
import os

from PySide6.QtWidgets import QMainWindow, QFileDialog, QApplication, QPushButton, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QCheckBox, QGridLayout, QSpinBox, QDoubleSpinBox, QSlider, QFormLayout, QSizePolicy, QSpacerItem, QTabWidget, QFrame, QScrollArea
from PySide6.QtGui import QPixmap, QImage, QPalette, QIcon
from PySide6 import QtCore
from PySide6.QtCore import QSize, Qt, QPointF

from PIL.ImageQt import ImageQt
from PIL import Image

import util
import pixelsort
import groupby
import pixelstats
import swizzle
import offset

from imagewidget import *

#--------------------------------------------------------------------------
# Glitch Parameter Input Widgets
#--------------------------------------------------------------------------

class PixelColorSliders(QWidget):
    """ Widget that gets user input intented for color_mods. Use getValue to get a tuple with three floats."""
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.layout = QFormLayout(self)
        title = QLabel("Modify Brightness")
        # NOTE can I clean this up by turning this into a loop instead of hard-coding 3 sliders?
        #      Just to cut down on the line count.
        reset_icon = QIcon.fromTheme("view-refresh")
        red_label = QLabel("Red")
        self.red_value = QLabel("0%")
        self.red_slider = QSlider()
        self.red_slider.setOrientation(Qt.Horizontal)
        self.red_slider.setMinimum(-100)
        self.red_slider.setMaximum(100)
        self.red_slider.valueChanged.connect(lambda v: self.red_value.setText(str(v) + "%"))
        self.red_slider.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))
        self.reset_red = QPushButton("-")
        self.reset_red.setMaximumWidth(16)
        self.reset_red.setMaximumHeight(16)
        self.reset_red.clicked.connect(lambda x: self.red_slider.setValue(0))

        green_label = QLabel("Green")
        self.green_value = QLabel("0%")
        self.green_slider = QSlider()
        self.green_slider.setOrientation(Qt.Horizontal)
        self.green_slider.setMinimum(-100)
        self.green_slider.setMaximum(100)
        self.green_slider.valueChanged.connect(lambda v: self.green_value.setText(str(v) + "%"))
        self.reset_green = QPushButton("-")
        self.reset_green.setMaximumWidth(16)
        self.reset_green.setMaximumHeight(16)
        self.reset_green.clicked.connect(lambda x: self.green_slider.setValue(0))

        blue_label = QLabel("Blue")
        self.blue_value = QLabel("0%")
        self.blue_slider = QSlider()
        self.blue_slider.setOrientation(Qt.Horizontal)
        self.blue_slider.setMinimum(-100)
        self.blue_slider.setMaximum(100)
        self.blue_slider.valueChanged.connect(lambda v: self.blue_value.setText(str(v) + "%"))
        self.reset_blue = QPushButton("-")
        self.reset_blue.setMaximumWidth(16)
        self.reset_blue.setMaximumHeight(16)
        self.reset_blue.clicked.connect(lambda x: self.blue_slider.setValue(0))

        self.layout.addRow(title)
        self.layout.addRow(red_label, self.red_value)
        self.layout.addRow(self.reset_red, self.red_slider)
        self.layout.addRow(green_label, self.green_value)
        self.layout.addRow(self.reset_green, self.green_slider)
        self.layout.addRow(blue_label, self.blue_value)
        self.layout.addRow(self.reset_blue, self.blue_slider)

    def getValues(self):
        red = (self.red_slider.value() / 100.0) + 1.0
        green = (self.green_slider.value() / 100.0) + 1.0
        blue = (self.blue_slider.value() / 100.0) + 1.0
        return (red, green, blue)

def combobox_with_keys(keys):
    """ Convenience function that creates a combobox,
    populates the options with items from an iterable, and returns the widget.
    """
    cb = QComboBox()
    for key in keys:
        cb.addItem(key)
    return cb

# Base class for widgets for different pixelsort region functions
# I will implement a class for each pixelsort function that has unique arguments
class GlitchFunctionArgs(QWidget):
    """
    Base class for widgets that take user input for pixelsort sort_function parameters.
    Each class in groupby.sort_functions should be mapped to a subclass of this, and calling
    get_kwargs returns suitable keyword arguments.
    """

    def __init__(self):
        super().__init__()

    def get_kwargs(self):
        raise NotImplementedError

class DiagonalArgs(GlitchFunctionArgs):
    """ Diagonal Group Parameters:
    Flip Slope: boolean
    """
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout(self)
        self.flip_slope_checkbox = QCheckBox("Flip Lines")
        self.layout.addWidget(self.flip_slope_checkbox)

    def get_kwargs(self):
        kwargs = dict()
        kwargs["flip_slope"] = self.flip_slope_checkbox.isChecked()
        return kwargs


class PxShutterSortArgs(GlitchFunctionArgs):
    """ Pixel-length Shutter Sort parameters:
            Shutter Width/Height: integer
    """

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.layout = QFormLayout(self)
        # TODO : limit size to the height / width of source image
        #        depending on whether the direction is rows / columns
        shutter_size_label = QLabel("Shutter Size:")
        self.shutter_size_input = QSpinBox()
        self.shutter_size_input.setValue(48)
        self.shutter_size_input.setSuffix("px")
        self.shutter_size_input.setMaximum(9999)

        self.layout.addRow(shutter_size_label, self.shutter_size_input)
        self.setLayout(self.layout)

    def get_kwargs(self):
        kwargs = dict()
        kwargs["shutter_size"] = self.shutter_size_input.value()
        return kwargs

class PxVariableShutterSortArgs(GlitchFunctionArgs):
    """ Variable Pixel-length Shutter Sort parameters:
            Min Shutter Width/Height: integer
            Max Shutter Width/Height: integer
    """

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.layout = QFormLayout(self)
        # TODO : limit size to the height / width of source image
        #        depending on whether the direction is rows / columns
        min_shutter_size_label = QLabel("Min Shutter Size:")
        self.min_shutter_size_input = QSpinBox()
        self.min_shutter_size_input.setValue(48)
        self.min_shutter_size_input.setSuffix("px")
        self.min_shutter_size_input.setMaximum(9999)

        max_shutter_size_label = QLabel("Max Shutter Size:")
        self.max_shutter_size_input = QSpinBox()
        self.max_shutter_size_input.setValue(48)
        self.max_shutter_size_input.setSuffix("px")
        self.max_shutter_size_input.setMaximum(9999)

        self.layout.addRow(min_shutter_size_label, self.min_shutter_size_input)
        self.layout.addRow(max_shutter_size_label, self.max_shutter_size_input)
        self.setLayout(self.layout)

    def get_kwargs(self):
        kwargs = dict()
        kwargs["min_size"] = self.min_shutter_size_input.value()
        kwargs["max_size"] = self.max_shutter_size_input.value()
        kwargs["seed"] = os.urandom(16) # This is a little overkill
        return kwargs


class PctShutterSortArgs(GlitchFunctionArgs):
    """ %-length Shutter Sort parameters:
            Shutter Width/Height: integer
    """

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.layout = QFormLayout(self)
        # TODO : limit size to the height / width of source image
        #        depending on whether the direction is rows / columns
        shutter_size_label = QLabel("Shutter Size:")
        self.shutter_size_input = QDoubleSpinBox()
        self.shutter_size_input.setValue(1.0)
        self.shutter_size_input.setSuffix("%")
        self.shutter_size_input.setMinimum(0.001)
        self.shutter_size_input.setMaximum(100.0)

        self.layout.addRow(shutter_size_label, self.shutter_size_input)
        self.setLayout(self.layout)

    def get_kwargs(self):
        kwargs = dict()
        kwargs["shutter_size"] = self.shutter_size_input.value() / 100.0
        return kwargs

class PctVariableShutterSortArgs(GlitchFunctionArgs):
    """ Variable %-length Shutter Sort parameters:
            Min Shutter Width/Height: double
            Max Shutter Width/Height: double
    """

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.layout = QFormLayout(self)
        # TODO : limit size to the height / width of source image
        #        depending on whether the direction is rows / columns
        min_shutter_size_label = QLabel("Min Shutter Size:")
        self.min_shutter_size_input = QDoubleSpinBox()
        self.min_shutter_size_input.setValue(1.0)
        self.min_shutter_size_input.setSuffix("%")
        self.min_shutter_size_input.setMinimum(0.001)
        self.min_shutter_size_input.setMaximum(100.0)

        max_shutter_size_label = QLabel("Max Shutter Size:")
        self.max_shutter_size_input = QDoubleSpinBox()
        self.max_shutter_size_input.setValue(1.0)
        self.max_shutter_size_input.setSuffix("%")
        self.max_shutter_size_input.setMinimum(0.001)
        self.max_shutter_size_input.setMaximum(100.0)

        self.layout.addRow(min_shutter_size_label, self.min_shutter_size_input)
        self.layout.addRow(max_shutter_size_label, self.max_shutter_size_input)
        self.setLayout(self.layout)

    def get_kwargs(self):
        kwargs = dict()
        kwargs["min_size"] = self.min_shutter_size_input.value() / 100.0
        kwargs["max_size"] = self.max_shutter_size_input.value() / 100.0
        kwargs["seed"] = os.urandom(16) # This is a little overkill
        return kwargs


class RandomSizeArgs(GlitchFunctionArgs):
    """ Random length sort parameters:
            Min Width/Height: double
            Max Width/Height: double
    """

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.layout = QFormLayout(self)
        # TODO : limit size to the height / width of source image
        #        depending on whether the direction is rows / columns
        min_size_label = QLabel("Min Size:")
        self.min_size_input = QDoubleSpinBox()
        self.min_size_input.setValue(1.0)
        self.min_size_input.setSuffix("%")
        self.min_size_input.setMinimum(0.001)
        self.min_size_input.setMaximum(100.0)

        max_size_label = QLabel("Max Size:")
        self.max_size_input = QDoubleSpinBox()
        self.max_size_input.setValue(1.0)
        self.max_size_input.setSuffix("%")
        self.max_size_input.setMinimum(0.001)
        self.max_size_input.setMaximum(100.0)

        self.layout.addRow(min_size_label, self.min_size_input)
        self.layout.addRow(max_size_label, self.max_size_input)
        self.setLayout(self.layout)

    def get_kwargs(self):
        kwargs = dict()
        kwargs["min_size"] = self.min_size_input.value() / 100.0
        kwargs["max_size"] = self.max_size_input.value() / 100.0
        kwargs["seed"] = None
        return kwargs


class TracerSortArgs(GlitchFunctionArgs):
    """ Tracer Sort parameters:
            Tracer Length: integer
            Color Mods: Tuple(float, float, float) that is used to modify the RGB pixel values in the tracers. Helps them stand out.
    """

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.layout = QFormLayout(self)
        # TODO : learn how to make tooltips that describe the parameters
        # TODO : limit size to the height / width of source image
        #        depending on whether the direction is rows / columns
        tracer_length_label = QLabel("Tracer Length:")
        self.tracer_length_input = QSpinBox()
        self.tracer_length_input.setSuffix("px")
        self.tracer_length_input.setValue(16)
        self.tracer_length_input.setMinimum(1)
        border_width_label = QLabel("Border Width:")
        self.border_width_input = QSpinBox()
        self.border_width_input.setSuffix("px")
        self.border_width_input.setValue(2)
        self.border_width_input.setMinimum(1)
        self.variance_threshold_label = QLabel("Variance Limit: 25%")
        self.variance_threshold_input = QSlider()
        self.variance_threshold_input.setValue(25)
        self.variance_threshold_input.setOrientation(Qt.Horizontal)
        self.variance_threshold_input.setMinimum(0)
        self.variance_threshold_input.setMaximum(100)
        self.variance_threshold_input.valueChanged.connect(lambda v: self.variance_threshold_label.setText(f'Variance Limit: {str(v)}%'))
        self.variance_threshold_input.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))

        self.layout.addRow(tracer_length_label, self.tracer_length_input)
        self.layout.addRow(border_width_label, self.border_width_input)
        self.layout.addRow(self.variance_threshold_label, self.variance_threshold_input)

        self.setLayout(self.layout)

    def get_kwargs(self):
        kwargs = dict()
        kwargs["tracer_length"] = self.tracer_length_input.value()
        kwargs["border_width"] = self.border_width_input.value()
        kwargs["variance_threshold"] = self.variance_threshold_input.value() / 100.0
        return kwargs

class NoParams(GlitchFunctionArgs):
    def get_kwargs(self):
        return {}

function_param_widgets = {
    "Linear": NoParams,
    "Rows": NoParams, "Columns": NoParams,
    "Diagonals": DiagonalArgs,
    "Wrapping Diagonals": NoParams,
    "Shutters (px)": PxShutterSortArgs, "Variable Shutters (px)": PxVariableShutterSortArgs,
    "Shutters (%)": PctShutterSortArgs, "Variable Shutters (%)": PctVariableShutterSortArgs,
    "Random": RandomSizeArgs,
    "Tracers": TracerSortArgs, "Wobbly Tracers": TracerSortArgs
    }

# Widgets for offset.py

class StaticOffsetArgs(GlitchFunctionArgs):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.layout = QFormLayout(self)
        self.offset_spinbox = QSpinBox()
        self.offset_spinbox.setSuffix("px")
        self.offset_spinbox.setValue(32)
        self.offset_spinbox.setMinimum(-5000)
        self.offset_spinbox.setMaximum(5000)

        self.layout.addRow("Offset:", self.offset_spinbox)

    def get_kwargs(self):
        kwargs = {}
        kwargs["offset"] = self.offset_spinbox.value()
        return kwargs

class WaveOffsetArgs(GlitchFunctionArgs):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.layout = QFormLayout(self)

        self.wave_height = QSpinBox()
        self.wave_height.setSuffix("px")
        self.wave_height.setValue(32)
        self.wave_height.setMinimum(-5000)
        self.wave_height.setMaximum(5000)

        self.wave_length = QSpinBox()
        self.wave_length.setSuffix("px")
        self.wave_length.setValue(32)
        self.wave_length.setMinimum(-5000)
        self.wave_length.setMaximum(5000)

        self.layout.addRow("Height:", self.wave_height)
        self.layout.addRow("Wavelength:", self.wave_length)

    def get_kwargs(self):
        kwargs = {}
        kwargs["height"] = self.wave_height.value()
        kwargs["inv_wavelength"] = 1.0 / self.wave_length.value()
        return kwargs

offset_param_widgets = {
        "Line Number": NoParams, "Static": StaticOffsetArgs,
        "Sine": WaveOffsetArgs, "Cosine": WaveOffsetArgs
        }

#--------------------------------------------------------------------------
# Glitch Input Containers
#--------------------------------------------------------------------------

class PixelSortInput(QWidget):
    """ Class for user input on Pixel Sorting. Can be used for single channel and RGB images.

    :param mode: bool that determines if image being sorted will be single or multi-channel.
                 it needs to know this because the sort key functions don't work with single-channel images.
    """

    def __init__(self, name, rgb=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rgb = rgb
        self.initUI(name)

    def initUI(self, name):
        self.layout = QFormLayout(self)
        self.layout.setAlignment(Qt.AlignCenter)

        # NOTE I use QWidgets as placeholders so that QFormLayout indexOf() and insertRow() does not break
        # when not in rgb mode.
        title = QLabel(name)
        if self.rgb:
            self.do_not_sort = QWidget()
        else:
            self.do_not_sort = QCheckBox("Do not sort")
        self.group_container = QFormLayout()
        groupby_label = QLabel("Delineate Pixels:")
        self.group_function_cb = combobox_with_keys(groupby.group_generators.keys())
        self.group_function_cb .currentTextChanged.connect(self.groupFunctionChanged)
        self.group_function_param_container = QVBoxLayout() # Because indexOf and insertRow are stupid
        self.group_function_params = NoParams()
        self.group_function_param_container.addWidget(self.group_function_params)

        self.group_container.addRow(groupby_label, self.group_function_cb)
        self.group_container.addRow(self.group_function_param_container)

        self.sort_container = QFormLayout()
        sort_function_label = QLabel("Group Pixels:")
        self.sort_function_cb = combobox_with_keys(groupby.sort_generators.keys())
        self.sort_function_cb.currentTextChanged.connect(self.sortFunctionChanged)
        self.sort_function_param_container = QVBoxLayout()
        self.sort_function_params = NoParams()
        self.sort_function_param_container.addWidget(self.sort_function_params)

        self.sort_container.addRow(sort_function_label, self.sort_function_cb)
        self.sort_container.addRow(self.sort_function_param_container)

        if self.rgb:
            sort_key_label = QLabel("Order Pixels By:")
            self.sort_key_function_cb = combobox_with_keys(pixelstats.key_functions.keys())

        self.reverse_checkbox = QCheckBox("Reverse Sort")


        self.layout.addRow(title, self.do_not_sort)
        group_and_sort_container = QVBoxLayout()
        group_and_sort_container.addLayout(self.group_container)
        group_and_sort_container.addLayout(self.sort_container)
        self.layout.addRow(group_and_sort_container)
        if self.rgb:
            self.layout.addRow(sort_key_label, self.sort_key_function_cb)
        self.layout.addRow(self.reverse_checkbox)

    def groupFunctionChanged(self, key):
        self.group_function_params.setParent(None)
        self.group_function_params = function_param_widgets[key]()
        self.group_function_param_container.addWidget(self.group_function_params)

    def sortFunctionChanged(self, key):
        self.sort_function_params.setParent(None)
        self.sort_function_params = function_param_widgets[key]()
        self.sort_function_param_container.addWidget(self.sort_function_params)

    def sortImage(self, source_image, color_mods, coords=None):
        if not self.rgb and self.do_not_sort.isChecked():
            return source_image
        group_function = self.group_function_cb.currentText()
        sort_function = self.sort_function_cb.currentText()
        if self.rgb:
            sort_key_function = self.sort_key_function_cb.currentText()
        else:
            sort_key_function = lambda x: x
        reverse = self.reverse_checkbox.checkState()
        kwargs = dict()
        kwargs.update(self.group_function_params.get_kwargs())
        kwargs.update(self.sort_function_params.get_kwargs())

        if coords:
            glitch_image = pixelsort.sort_part(
                                source_image,
                                coords,
                                group_function,
                                sort_function,
                                sort_key_function,
                                reverse, color_mods, **kwargs
                                )
        else:
            glitch_image = pixelsort.sort_image(
                                source_image,
                                group_function,
                                sort_function,
                                sort_key_function,
                                reverse, color_mods, **kwargs
                                )
        return glitch_image

class LineOffsetInput(QWidget):
    """ Class for user input of Line Offsets. Can be used for single channel and RGB images.
    """

    def __init__(self, name, rgb=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rgb = rgb
        self.initUI(name)

    def initUI(self, name):
        self.layout = QFormLayout(self)
        self.layout.setAlignment(Qt.AlignCenter)

        # NOTE I use QWidgets as placeholders so that QFormLayout indexOf() and insertRow() does not break
        # when not in rgb mode.
        title = QLabel(name)
        self.group_container = QFormLayout()
        groupby_label = QLabel("Lines:")
        self.line_function_cb = combobox_with_keys(groupby.group_generators.keys())
        self.line_function_cb.currentTextChanged.connect(self.groupFunctionChanged)
        self.line_function_param_container = QVBoxLayout() # Because indexOf and insertRow are stupid
        self.line_function_params = NoParams()
        self.line_function_param_container.addWidget(self.line_function_params)

        self.group_container.addRow(groupby_label, self.line_function_cb)
        self.group_container.addRow(self.line_function_param_container)

        self.line_function_cb.setCurrentText("Rows") # 'Linear' is a bad default

        self.offset_container = QFormLayout()
        offset_label = QLabel("Offset Function:")
        self.offset_cb = combobox_with_keys(offset.offset_functions.keys())
        self.offset_cb.currentTextChanged.connect(self.offsetFunctionChanged)
        self.offset_param_container = QVBoxLayout()
        self.offset_params = NoParams()
        self.offset_param_container.addWidget(self.offset_params)

        self.offset_container.addRow(offset_label, self.offset_cb)
        self.offset_container.addRow(self.offset_param_container)

        if self.rgb:
            self.layout.addRow(title)
        else:
            self.do_not_glitch = QCheckBox("Ignore channel")
            self.layout.addRow(title, self.do_not_glitch)
        line_and_offset_container = QVBoxLayout()
        line_and_offset_container.addLayout(self.group_container)
        line_and_offset_container.addLayout(self.offset_container)
        self.layout.addRow(line_and_offset_container)

    def groupFunctionChanged(self, key):
        self.line_function_params.setParent(None)
        self.line_function_params = function_param_widgets[key]()
        self.group_container.addWidget(self.line_function_params)

    def offsetFunctionChanged(self, key):
        self.offset_params.setParent(None)
        self.offset_params = offset_param_widgets[key]()
        self.offset_param_container.addWidget(self.offset_params)

    def offsetImage(self, source_image, coords=None):
        if not self.rgb and self.do_not_glitch.isChecked():
            return source_image
        line_function = self.line_function_cb.currentText()
        offset_function = self.offset_cb.currentText()

        kwargs = dict()
        kwargs.update(self.line_function_params.get_kwargs())
        kwargs.update(self.offset_params.get_kwargs())

        glitch_image = offset.offset(
                                source_image,
                                line_function,
                                offset_function,
                                coords=coords,
                                **kwargs
                                )
        return glitch_image


class GlitchWidget(QWidget):
    """ Base class for widgets that execute glitches in GitchArtTools.
    Any subclass of this must implement a method performGlitch(source_image:str) which returns a PIL Image
    """
    def performGlitch(self, source_image):
        raise NotImplementedError

class PixelSortWidget(GlitchWidget):
    can_use_region = True
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._bandsort = False
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout(self)

        expanding_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.sort_bands_checkbox = QCheckBox("Sort channels separately")
        self.sort_bands_checkbox.stateChanged.connect(self.channelsChanged)
        self.input_container = QWidget()
        self.input_container.setSizePolicy(expanding_policy)
        self.input_layout = QVBoxLayout(self.input_container)
        self.pixelsort_input = []
        self.loadInputWidgets()
        self.scrollarea = QScrollArea()
        self.scrollarea.setWidgetResizable(True)
        self.scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollarea.setSizePolicy(expanding_policy)
        self.scrollarea.setWidget(self.input_container)

        color_mod_label = QLabel("Modify Sorted Pixels:")
        self.color_mod_input = PixelColorSliders()

        self.layout.addWidget(self.sort_bands_checkbox, Qt.AlignTop)#, 0, 0)
        self.layout.addWidget(self.scrollarea)#, 1, 0)
        self.layout.addWidget(self.color_mod_input, Qt.AlignTop)#, 2, 0)
        self.layout.setStretch(0, 0)
        self.layout.setStretch(1, 2)
        self.layout.setStretch(2, 0)

        self.setAutoFillBackground(True)
        self.setBackgroundRole(QPalette.AlternateBase)


    def channelsChanged(self, checked):
        self._bandsort = checked
        self.loadInputWidgets()

    def loadInputWidgets(self):
        for input_widget in self.pixelsort_input:
            input_widget.setParent(None)
            input_widet = None
        if self._bandsort:
            # Bandsort
            red_input = PixelSortInput("Red", rgb=False)
            red_input.setAutoFillBackground(True)
            red_input.setBackgroundRole(QPalette.Light)
            green_input = PixelSortInput("Green", rgb=False)
            green_input.setAutoFillBackground(True)
            green_input.setBackgroundRole(QPalette.Midlight)
            blue_input = PixelSortInput("Blue", rgb=False)
            blue_input.setAutoFillBackground(True)
            blue_input.setBackgroundRole(QPalette.Light)
            self.pixelsort_input = [red_input, green_input, blue_input]
        else:
            # RGB Pixelsort
            rgb_input = PixelSortInput("3-Channel", rgb=True)
            self.pixelsort_input = [rgb_input]
        for widget in self.pixelsort_input:
            widget.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))
            self.input_layout.addWidget(widget)

    def performGlitch(self, source_filename, coords=None):
        source_image = Image.open(source_filename)
        color_mods = self.color_mod_input.getValues()
        if self._bandsort:
            bands = []
            for band, band_input, mod in zip(source_image.split(), self.pixelsort_input, color_mods):
                band_glitch = band_input.sortImage(band, mod, coords)
                bands.append(band_glitch)
            glitch_image = Image.merge("RGB", tuple(bands))
        else:
            glitch_image = self.pixelsort_input[0].sortImage(source_image, color_mods, coords)
        return glitch_image


class SwizzleWidget(GlitchWidget):
    """Widget to get input for swizzling, or channel-swapping.
        Params: swaps
    """
    can_use_region = True
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initUI()

    def initUI(self):
        self.layout = QFormLayout(self)

        red_label = QLabel("Red")
        green_label = QLabel("Green")
        blue_label = QLabel("Blue")

        rgb = ("R", "G", "B")
        self.red_swap = combobox_with_keys(rgb)
        self.green_swap = combobox_with_keys(rgb)
        self.green_swap.setCurrentText("G")
        self.blue_swap = combobox_with_keys(rgb)
        self.blue_swap.setCurrentText("B")

        self.layout.addRow("Pixels", QLabel("Destination Channel"))
        self.layout.addRow(self.red_swap, red_label)
        self.layout.addRow(self.green_swap, green_label)
        self.layout.addRow(self.blue_swap, blue_label)

    def performGlitch(self, source_filename, coords=None):
        swaps = f'{self.red_swap.currentText()}{self.green_swap.currentText()}{self.blue_swap.currentText()}'
        return swizzle.swizzle(source_filename, swaps, coords)


class LineOffsetWidget(GlitchWidget):
    """ Widget that rotates/offsets lines in an image. """
    can_use_region = True

    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self._splitbands = False
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout(self)

        self.split_bands_checkbox = QCheckBox("Separate Bands")
        self.split_bands_checkbox.stateChanged.connect(self.channelsChanged)

        expanding_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.input_container = QWidget()
        self.input_container.setSizePolicy(expanding_policy)
        self.input_layout = QVBoxLayout(self.input_container)
        self.offset_input = []
        self.loadInputWidgets()
        self.scrollarea = QScrollArea()
        self.scrollarea.setWidgetResizable(True)
        self.scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollarea.setSizePolicy(expanding_policy)
        self.scrollarea.setWidget(self.input_container)

        self.layout.addWidget(self.split_bands_checkbox, Qt.AlignTop)#, 0, 0)
        self.layout.addWidget(self.scrollarea)#, 1, 0)
        self.layout.setStretch(0, 0)
        self.layout.setStretch(1, 2)

        self.setAutoFillBackground(True)
        self.setBackgroundRole(QPalette.AlternateBase)


    def channelsChanged(self, checked):
        self._splitbands = checked
        self.loadInputWidgets()

    def loadInputWidgets(self):
        for input_widget in self.offset_input:
            input_widget.setParent(None)
            input_widet = None
        if self._splitbands:
            # Bandsort
            red_input = LineOffsetInput("Red", False)
            red_input.setAutoFillBackground(True)
            red_input.setBackgroundRole(QPalette.Light)
            green_input = LineOffsetInput("Green", False)
            green_input.setAutoFillBackground(True)
            green_input.setBackgroundRole(QPalette.Midlight)
            blue_input = LineOffsetInput("Blue", False)
            blue_input.setAutoFillBackground(True)
            blue_input.setBackgroundRole(QPalette.Light)
            self.offset_input = [red_input, green_input, blue_input]
        else:
            # RGB Pixelsort
            rgb_input = LineOffsetInput("3-Channel")
            self.offset_input = [rgb_input]
        for widget in self.offset_input:
            widget.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))
            self.input_layout.addWidget(widget)

    def performGlitch(self, source_filename, coords=None):
        source_image = Image.open(source_filename)
        if self._splitbands:
            bands = []
            for band, band_input in zip(source_image.split(), self.offset_input):
                band_glitch = band_input.offsetImage(band, coords)
                bands.append(band_glitch)
            glitch_image = Image.merge("RGB", tuple(bands))
        else:
            glitch_image = self.offset_input[0].offsetImage(source_image, coords)
        return glitch_image


glitch_widget_map = {"Pixelsort": PixelSortWidget, "Swizzle": SwizzleWidget, "Line Offsets": LineOffsetWidget}

#--------------------------------------------------------------------------
# Main Application
#--------------------------------------------------------------------------

class GlitchArtTools(QWidget):

    def __init__(self, screen_size):
        super().__init__()

        self.default_path = util.get_default_image_path()
        self.source_filename = None
        self.glitch_filename = None
        self._size_hint = screen_size
        self.default_pixmap_max_size = self.sizeHint() * 3 / 8

        self.initUI()
        self.setWindowTitle("Glitch Art Tools - Pixel Sorting")

    def sizeHint(self):
        return self._size_hint

    def initUI(self):
        self.main_layout = QHBoxLayout()

        self.image_tabs = QTabWidget()

        self.image_input_tab = QWidget()
        image_input_layout = QVBoxLayout(self.image_input_tab)
        image_select_hbox = QHBoxLayout()
        file_select_label = QLabel("Glitch Input:")
        self.image_source_input = QLineEdit()
        self.image_source_input.setPlaceholderText("Source Image")
        self.image_source_input.editingFinished.connect(self.setImageFromLineInput)
        file_browser_button = QPushButton("Browse...")
        file_browser_button.clicked.connect(self.openFileSelect)
        self.source_image_viewer = ScrollableImageViewer()
        self.source_image_viewer.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding))
        image_select_hbox.addWidget(file_select_label)
        image_select_hbox.addWidget(self.image_source_input)
        image_select_hbox.addWidget(file_browser_button)

        image_input_layout.addLayout(image_select_hbox)
        image_input_layout.addWidget(self.source_image_viewer)

        self.image_output_tab = QWidget()
        image_output_layout = QVBoxLayout(self.image_output_tab)
        glitch_file_hbox = QHBoxLayout()
        self.enlarge_glitch_image = QPushButton("Enlarge") # TODO change to 'expand' icon
        self.enlarge_glitch_image.clicked.connect(lambda _: self.openImageInNewWindow("glitch"))
        self.swap_glitch_button = QPushButton("Use As Input")
        self.swap_glitch_button.setEnabled(False)
        self.swap_glitch_button.clicked.connect(self.setGlitchAsSource)
        self.save_glitch_copy = QPushButton("Save As...")
        self.save_glitch_copy.clicked.connect(self.openSaveAs)
        self.save_glitch_copy.setEnabled(False)
        glitch_file_hbox.addWidget(self.enlarge_glitch_image)
        glitch_file_hbox.addWidget(self.swap_glitch_button)
        glitch_file_hbox.addWidget(self.save_glitch_copy)
        self.glitch_image_viewer = ScrollableImageViewer()
        self.glitch_image_viewer.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding))

        image_output_layout.addLayout(glitch_file_hbox)
        image_output_layout.addWidget(self.glitch_image_viewer)

        self.image_tabs.addTab(self.image_input_tab, "Input")
        self.image_tabs.addTab(self.image_output_tab, "Output")

        self.settings_container = QWidget()
        self.settings_layout = QVBoxLayout(self.settings_container)
        self.settings_layout.setAlignment(Qt.AlignCenter)
        glitch_choice_container = QHBoxLayout()
        glitch_settings_label = QLabel("Glitch Settings")
        glitch_settings_label.setSizePolicy(QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum))
        self.glitch_choice_cb = QComboBox()
        for key in glitch_widget_map.keys():
            self.glitch_choice_cb.addItem(key)
        # TODO add a control for the type of glitch to perform and make this more abstract.
        glitch_choice_container.addWidget(glitch_settings_label, Qt.AlignLeft)
        glitch_choice_container.addWidget(self.glitch_choice_cb, Qt.AlignRight)
        self.glitch_choice_cb.currentTextChanged.connect(self.setGlitchWidget)
        self.glitch_widget = None

        self.glitch_it_button = QPushButton("Glitch It")
        self.glitch_it_button.setMaximumWidth(144)
        self.glitch_it_button.setEnabled(False)
        self.glitch_it_button.clicked.connect(self.performGlitch)

        self.settings_layout.addLayout(glitch_choice_container, Qt.AlignTop | Qt.AlignLeft)
        self.setGlitchWidget(self.glitch_choice_cb.currentText())
        self.settings_layout.addWidget(self.glitch_it_button, Qt.AlignCenter)
        self.settings_container.setLayout(self.settings_layout)
        self.settings_container.setMinimumWidth(320)

        self.settings_layout.setStretch(1, 1)

        # Sizing
        settings_sp = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.settings_container.setSizePolicy(settings_sp)

        main_sp = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.image_tabs.setSizePolicy(main_sp)

        self.main_layout.addWidget(self.settings_container)
        self.main_layout.addWidget(self.image_tabs)
        self.main_layout.setStretch(0, 1)
        self.main_layout.setStretch(1, 5)
        self.setLayout(self.main_layout)

    def setGlitchWidget(self, key):
        index = self.settings_layout.indexOf(self.glitch_it_button) - 1
        if self.glitch_widget:
            self.glitch_widget.setParent(None)
        self.glitch_widget = glitch_widget_map[key]()
        self.settings_layout.insertWidget(index, self.glitch_widget)
        self.source_image_viewer.setSelectionEnabled(self.glitch_widget.can_use_region)

    def getMaxImageSize(self):
        return self.frameSize() / 2

    def openImageInNewWindow(self, q_image):
        if q_image == "glitch":
            filename = self.glitch_filename
        self.temp_window = ScrollableImageViewer(filename)
        self.temp_window.show()

    def setImageFromLineInput(self):
        if os.path.exists(filename := self.image_source_input.text()):
            self.setSourceImage(filename)

    def openFileSelect(self):
        # NOTE : find a better way to have default paths - it's kind of annoying having to navigate to pictures every time
        if self.source_filename:
            start_dir = os.path.dirname(self.source_filename) # If there is already a filename, open with the path to its directory
        else:
            start_dir = os.path.join(self.default_path, "input")
        filename = QFileDialog.getOpenFileName(self, 'Select Image', start_dir, "Image Files (*.png *.jpg *.bmp)")
        if(filename[0]):
            self.setSourceImage(filename[0])

    def openSaveAs(self):
        start_dir = os.path.join(self.default_path, "output")
        filename = QFileDialog.getSaveFileName(self, 'Save Image as', start_dir, "Image Files (*.png *.jpg *.bmp)")
        if filename[0]:
            self.saveGlitchCopy(filename[0])

    def setSourceImage(self, filename, clear_region=True):
        self.source_filename = filename
        self.image_source_input.setText(self.source_filename)
        self.source_image_viewer.setImage(self.source_filename, clear_region)
        self.glitch_it_button.setEnabled(True)

    # NOTE
    # For some reason using ImageQt to convert the PIL Image to a QImage and then
    # using QPixmap.fromImage causes the pixmap to be translucent
    # So for now I don't do that. Instead I just load the pixmap using the filename
    # This is why util.make_temp_image sets the pil_image.filename
    def setGlitchImage(self, pil_image):
        self.glitch_qimage = ImageQt(pil_image)
        self.glitch_filename = pil_image.filename
        self.glitch_image_viewer.setImage(self.glitch_filename)
        self.swap_glitch_button.setEnabled(True)
        self.save_glitch_copy.setEnabled(True)

    def setGlitchAsSource(self):
        self.image_tabs.setCurrentWidget(self.image_input_tab)
        self.setSourceImage(self.glitch_filename, False)

    def saveGlitchCopy(self, file_destination):
        # NOTE should I swap the temp glitch filename with the permanent filename after this?
        #      I feel like I _should_ but also, why not continue to use the temp?
        saved = self.glitch_qimage.save(file_destination)
        if not saved:
            # TODO : make qt message box popup
            print(f"File ({file_destination}) not saved...")
            #not_saved_message = QMessageBox("

    def performGlitch(self):
        if self.glitch_filename and not (self.glitch_filename == self.source_filename):
            # NOTE : improve file deletion
            self.deleteImage(self.glitch_filename)
        coords = None
        coords_rect = self.source_image_viewer.rb_rect
        if coords_rect:
            coords = (coords_rect.x(), coords_rect.y(), coords_rect.x() + coords_rect.width(), coords_rect.y() + coords_rect.height())

        glitch_image = self.glitch_widget.performGlitch(self.source_filename, coords)
        util.make_temp_file(glitch_image, os.path.join(self.default_path, "temp"))
        self.image_tabs.setCurrentWidget(self.image_output_tab)
        self.setGlitchImage(glitch_image)

    def deleteImage(self, filename):
        if os.path.exists(filename):
            os.remove(filename)


def main():
    app = QApplication(sys.argv)
    screen = app.primaryScreen()
    w = GlitchArtTools(screen.size())
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
