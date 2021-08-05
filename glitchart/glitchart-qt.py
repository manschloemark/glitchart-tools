""" glitchart-qt - Qt GUI for glitch art tools. Uses PySide6."""
# Copyright (c) 2021 Mark Schloeman

from PySide6.QtWidgets import QMainWindow, QFileDialog, QApplication, QPushButton, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QCheckBox, QGridLayout, QSpinBox, QDoubleSpinBox, QSlider, QFormLayout, QSizePolicy, QSpacerItem, QTabWidget
from PySide6.QtGui import QPixmap, QImage, QPalette
from PySide6 import QtCore
from PySide6.QtCore import QSize, Qt, QPointF
from PIL.ImageQt import ImageQt
from PIL import Image
import sys
import os
import util
import pixelsort
import groupby
import pixelstats

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
        # NOTE can I clean this up by turning this into a loop instead of hard-coding 3 sliders?
        #      Just to cut down on the line count.
        red_label = QLabel("Red")
        self.red_value = QLabel("0%")
        self.red_slider = QSlider()
        self.red_slider.setOrientation(Qt.Horizontal)
        self.red_slider.setMinimum(-100)
        self.red_slider.setMaximum(100)
        self.red_slider.valueChanged.connect(lambda v: self.red_value.setText(str(v) + "%"))
        self.reset_red = QPushButton()
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
        self.reset_green = QPushButton()
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
        self.reset_blue = QPushButton()
        self.reset_blue.setMaximumWidth(16)
        self.reset_blue.setMaximumHeight(16)
        self.reset_blue.clicked.connect(lambda x: self.blue_slider.setValue(0))

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
class PixelsortRegionArgs(QWidget):
    """
    Base class for widgets that take user input for pixelsort sort_function parameters.
    Each class in groupby.sort_functions should be mapped to a subclass of this, and calling
    get_kwargs returns suitable keyword arguments.
    """

    def __init__(self):
        super().__init__()

    def get_kwargs(self):
        raise NotImplementedError

class DiagonalArgs(PixelsortRegionArgs):
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


class PxShutterSortArgs(PixelsortRegionArgs):
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

class PxVariableShutterSortArgs(PixelsortRegionArgs):
    """ Variable Pixel-length Shutter Sort parameters:
            Shutter Direction: rows / column generator from glitchart module
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
        return kwargs


class PctShutterSortArgs(PixelsortRegionArgs):
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

class PctVariableShutterSortArgs(PixelsortRegionArgs):
    """ Variable %-length Shutter Sort parameters:
            Shutter Direction: rows / column generator from glitchart module
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
        return kwargs


class TracerSortArgs(PixelsortRegionArgs):
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

class NoParams(PixelsortRegionArgs):
    def get_kwargs(self):
        return {}

function_param_widgets = {
    "Linear": NoParams,
    "Rows": NoParams, "Columns": NoParams,
    "Diagonals": DiagonalArgs,
    "Wrapping Diagonals": NoParams,
    "Shutters (px)": PxShutterSortArgs, "Variable Shutters (px)": PxVariableShutterSortArgs,
    "Shutters (%)": PctShutterSortArgs, "Variable Shutters (%)": PctVariableShutterSortArgs,
    "Tracers": TracerSortArgs, "Wobbly Tracers": TracerSortArgs
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
            sort_key_container = QHBoxLayout()
            sort_key_container.addWidget(self.sort_key_function_cb)
            sort_key_container.addWidget(self.reverse_checkbox)
            self.layout.addRow(sort_key_label, sort_key_container)
        else:
            self.layout.addRow(self.reverse_checkbox)

    def groupFunctionChanged(self, key):
        self.group_function_params.setParent(None)
        self.group_function_params = function_param_widgets[key]()
        self.group_function_param_container.addWidget(self.group_function_params)

    def sortFunctionChanged(self, key):
        self.sort_function_params.setParent(None)
        self.sort_function_params = function_param_widgets[key]()
        self.sort_function_param_container.addWidget(self.sort_function_params)

    def sortImage(self, source_image, color_mods):
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

        glitch_image = pixelsort.sort_image(
                                source_image,
                                group_function,
                                sort_function,
                                sort_key_function,
                                reverse, color_mods, **kwargs
                                )
        return glitch_image

class PixelSortWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._bandsort = False
        self.initUI()
    
    def initUI(self):
        self.layout = QGridLayout(self)

        self.sort_bands_checkbox = QCheckBox("Sort channels separately")
        self.sort_bands_checkbox.stateChanged.connect(self.channelsChanged)
        self.pixelsort_input_container = QVBoxLayout()
        self.pixelsort_input = []
        self.loadInputWidgets()

        color_mod_label = QLabel("Modify Sorted Pixels:")
        self.color_mod_input = PixelColorSliders()

        self.layout.addWidget(self.sort_bands_checkbox, 0, 0, Qt.AlignLeft)
        self.layout.addLayout(self.pixelsort_input_container, 1, 0, 3, 1, Qt.AlignCenter)
        self.layout.addWidget(self.color_mod_input, 4, 0, 1, 2, Qt.AlignCenter)

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
            # NOTE keeping pixelsort_input as a list so I can do 'for ... in pixelsort_input'
            #      not sure if this is smart at all but it saves a few loc.
            self.pixelsort_input = [rgb_input]
        for widget in self.pixelsort_input:
            self.pixelsort_input_container.addWidget(widget)
    
    # NOTE: I'm not sure which class should handle the call to pixelsort.
    #       I think I'll try this way and then if it's slow I'll try the inverse.
    def performGlitch(self, source_filename):
        source_image = Image.open(source_filename)
        color_mods = self.color_mod_input.getValues()
        if self._bandsort:
            bands = []
            for band, band_input, mod in zip(source_image.split(), self.pixelsort_input, color_mods):
                band_glitch = band_input.sortImage(band, mod)
                bands.append(band_glitch)
            glitch_image = Image.merge("RGB", tuple(bands))
        else:
            glitch_image = self.pixelsort_input[0].sortImage(source_image, color_mods)
        return glitch_image


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
        self.source_image_view = ScrollableImageViewer()
        self.source_image_view.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding))
        image_select_hbox.addWidget(file_select_label)
        image_select_hbox.addWidget(self.image_source_input)
        image_select_hbox.addWidget(file_browser_button)

        image_input_layout.addLayout(image_select_hbox)
        image_input_layout.addWidget(self.source_image_view)

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
        self.glitch_image_view = ScrollableImageViewer()
        self.glitch_image_view.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding))

        image_output_layout.addLayout(glitch_file_hbox)
        image_output_layout.addWidget(self.glitch_image_view)

        self.image_tabs.addTab(self.image_input_tab, "Input")
        self.image_tabs.addTab(self.image_output_tab, "Output")

        self.settings_container = QWidget()
        self.settings_layout = QVBoxLayout(self.settings_container)
        self.settings_layout.setAlignment(Qt.AlignCenter)
        glitch_settings_label = QLabel("Glitch Settings")
        glitch_settings_label.setSizePolicy(QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum))
        # TODO add a control for the type of glitch to perform and make this more abstract.
        self.glitch_widget = PixelSortWidget()
        self.glitch_it_button = QPushButton("Glitch It")
        self.glitch_it_button.setMaximumWidth(144)
        self.glitch_it_button.setEnabled(False)
        self.glitch_it_button.clicked.connect(self.performGlitch)

        self.settings_layout.addWidget(glitch_settings_label, Qt.AlignTop | Qt.AlignLeft)
        self.settings_layout.addWidget(self.glitch_widget)
        self.settings_layout.addWidget(self.glitch_it_button, Qt.AlignCenter)
        self.settings_container.setLayout(self.settings_layout)

        self.main_layout.addWidget(self.settings_container)
        self.main_layout.addWidget(self.image_tabs)
        self.setLayout(self.main_layout)

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

    def setSourceImage(self, filename):
        self.source_filename = filename
        self.image_source_input.setText(self.source_filename)
        self.source_image_view.setImage(self.source_filename)
        self.glitch_it_button.setEnabled(True)

    # NOTE
    # For some reason using ImageQt to convert the PIL Image to a QImage and then
    # using QPixmap.fromImage causes the pixmap to be translucent
    # So for now I don't do that. Instead I just load the pixmap using the filename
    # This is why util.make_temp_image sets the pil_image.filename
    def setGlitchImage(self, pil_image):
        self.glitch_qimage = ImageQt(pil_image)
        self.glitch_filename = pil_image.filename
        self.glitch_image_view.setImage(self.glitch_filename)
        self.swap_glitch_button.setEnabled(True)
        self.save_glitch_copy.setEnabled(True)

    def setGlitchAsSource(self):
        self.image_tabs.setCurrentWidget(self.image_input_tab)
        self.setSourceImage(self.glitch_filename)

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
        glitch_image = self.glitch_widget.performGlitch(self.source_filename)
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
