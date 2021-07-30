""" glitchart-qt - Qt GUI for glitch art tools. Uses PySide6."""
# Copyright (c) 2021 Mark Schloeman

from PySide6.QtWidgets import QMainWindow, QFileDialog, QApplication, QPushButton, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QCheckBox, QGridLayout, QSpinBox, QSlider, QGraphicsScene, QGraphicsView, QFormLayout
from PySide6.QtGui import QPixmap, QImage
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

# NOTE: maybe I should split this up into multiple modules for readability

#--------------------------------------------------------------------------
# Image Viewing Widgets
#--------------------------------------------------------------------------

class ScrollableImageViewer(QWidget):
    def __init__(self, filename):
        super().__init__()
        self.loadUI()
        self.setPixmap(filename)

    def loadUI(self):
        self.layout = QVBoxLayout(self)

        self.scene = QGraphicsScene()
        self.view = ZoomableGraphicsView(self.scene)
        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

        self.layout.addWidget(self.view)

    def setPixmap(self, filename):
        self.zoom_level = 1.0
        self.source_pixmap = QPixmap(filename)
        self.scene_pixmap = self.source_pixmap
        self.updateView()

    def updateView(self, center=None):
        self.scene.clear()
        self.scene.addPixmap(self.scene_pixmap)
        if center:
            self.view.centerOn(center)


class ZoomableGraphicsView(QGraphicsView):
    def wheelEvent(self, event):
        zoom_delta = event.angleDelta().y() / 8.0 / 360.0
        new_zoom = 1.0 + zoom_delta
        self.scale(new_zoom, new_zoom)


class ResizableImageWindow(QWidget):
    def __init__(self, filename):
        super().__init__()
        self.source_pixmap = QPixmap(filename)
        self.initUI()

    def initUI(self):
        self.layout = QHBoxLayout(self)
        self.image_label = QLabel()
        self.display_pixmap = self.source_pixmap.scaled(self.source_pixmap.size().boundedTo(self.size()), Qt.KeepAspectRatio)
        self.image_label.setPixmap(self.display_pixmap)

        self.layout.addWidget(self.image_label, Qt.AlignCenter)

    def resizeEvent(self, event):
        self.display_pixmap = self.source_pixmap.scaled(self.size() * 0.98, Qt.KeepAspectRatio)
        self.image_label.setPixmap(self.display_pixmap)


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


#class PixelsortRegionComboBox(QComboBox):
#    """ QComboBox that loads all grouping function keys for the user to select """
#
#    def __init__(self):
#        super().__init__()
#        self.initUI()
#
#    def initUI(self):
#        for region_function_name in glitchart.grouping_functions.keys():
#            self.addItem(region_function_name)


#class PixelsortFunctionCombobox(QComboBox):
#    """ QComboBox that loads all sort function keys for the user to select """
#
#    def __init__(self):
#        super().__init__()
#        self.initUI()
#
#    def initUI(self):
#        for sort_function_name in glitchart.sort_functions.keys():
#            self.addItem(sort_function_name)


#class PixelsortKeyComboBox(QComboBox):
#    """QComboBox that loads all pixel sorting key function names for the user to select. """
#
#    def __init__(self):
#        super().__init__()
#        self.initUI()
#
#    def initUI(self):
#        for pixel_key_function_name in pixelstats.key_functions.keys():
#            self.addItem(pixel_key_function_name)

# The classes above feel unnecessary. A factory function should suffice.
def combobox_with_keys(keys):
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

class ShutterSortArgs(PixelsortRegionArgs):
    """ Shutter Sort parameters:
            Shutter Direction: rows / column generator from glitchart module
            Shutter Width/Height: integer
    """

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout(self)
        title = QLabel("Shutter Sort Parameters")
        # TODO : limit size to the height / width of source image
        #        depending on whether the direction is rows / columns
        shutter_size_label = QLabel("Shutter Size:")
        self.shutter_size_input = QSpinBox()
        self.shutter_size_input.setValue(48)
        self.shutter_size_input.setSuffix("px")
        self.shutter_size_input.setMaximum(9999)

        self.layout.addWidget(title)
        self.layout.addWidget(shutter_size_label)
        self.layout.addWidget(self.shutter_size_input)
        self.setLayout(self.layout)

    def get_kwargs(self):
        kwargs = dict()
        kwargs["shutter_size"] = self.shutter_size_input.value()
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
        self.layout = QVBoxLayout(self)
        title = QLabel("Tracer Sort Parameters")
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

        self.layout.addWidget(title)
        self.layout.addWidget(tracer_length_label)
        self.layout.addWidget(self.tracer_length_input)
        self.layout.addWidget(border_width_label)
        self.layout.addWidget(self.border_width_input)
        self.layout.addWidget(self.variance_threshold_label)
        self.layout.addWidget(self.variance_threshold_input)

        self.setLayout(self.layout)

    def get_kwargs(self):
        kwargs = dict()
        kwargs["tracer_length"] = self.tracer_length_input.value()
        kwargs["border_width"] = self.border_width_input.value()
        kwargs["variance_threshold"] = self.variance_threshold_input.value() / 100.0
        return kwargs

def no_params():
    return None

function_param_widgets = {
    "Linear": no_params,
    "Rows": no_params, "Columns": no_params,
    "Shutters": ShutterSortArgs,
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
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignCenter)

        title = QLabel(name)
        groupby_label = QLabel("Delineate image by: ")
        self.group_function_cb = combobox_with_keys(groupby.group_generators.keys())
        self.group_function_cb .currentTextChanged.connect(self.groupFunctionChanged)

        sort_function_label = QLabel("Sort image by: ")
        self.sort_function_cb = combobox_with_keys(groupby.sort_generators.keys())
        self.sort_function_cb.currentTextChanged.connect(self.sortFunctionChanged)
        self.sort_function_params = None # TODO find out what this does?

        if self.rgb:
            sort_key_label = QLabel("Order Pixels By:")
            self.sort_key_function_cb = combobox_with_keys(pixelstats.key_functions.keys())

        self.reverse_checkbox = QCheckBox("Reversed")

        color_mod_label = QLabel("Modify Sorted Pixels:")
        self.color_mod_input = PixelColorSliders()

        self.layout.addWidget(title)
        self.layout.addWidget(groupby_label)
        self.layout.addWidget(self.group_function_cb)
        self.layout.addWidget(sort_function_label)
        self.layout.addWidget(self.sort_function_cb)
        if self.rgb:
            self.layout.addWidget(sort_key_label)
            self.layout.addWidget(self.sort_key_function_cb)
        self.layout.addWidget(self.reverse_checkbox)
        self.layout.addWidget(color_mod_label)
        self.layout.addWidget(self.color_mod_input)
    
    def groupFunctionChanged(self, key):
        pass

    def sortFunctionChanged(self, key):
        if self.sort_function_params:
            self.sort_function_params.setParent(None)
        self.sort_function_params = function_param_widgets[key]()
        if self.sort_function_params:
            self.layout.insertWidget(
                                self.layout.indexOf(self.sort_function_cb) + 1,
                                self.sort_function_params
                                )
    
    def performGlitch(self, source_image):
        group_function = self.group_function_cb.currentText()
        sort_function = self.sort_function_cb.currentText()
        if self.rgb:
            sort_key_function = self.sort_key_function_cb.currentText()
        else:
            sort_key_function = lambda x: x
        reverse = self.reverse_checkbox.checkState()
        color_mods = self.color_mod_input.getValues()
        kwargs = dict()
        if self.sort_function_params:
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
        self.layout = QVBoxLayout(self)

        self.sort_bands_checkbox = QCheckBox("Sort channels separately")
        self.sort_bands_checkbox.stateChanged.connect(self.channelsChanged)
        self.pixelsort_input_container = QVBoxLayout()
        self.pixelsort_input = []
        self.loadInputWidgets()

        self.layout.addWidget(self.sort_bands_checkbox)
        self.layout.addLayout(self.pixelsort_input_container)

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
            green_input = PixelSortInput("Green", rgb=False)
            blue_input = PixelSortInput("Blue", rgb=False)
            self.pixelsort_input = [red_input, green_input, blue_input]
        else:
            # RGB Pixelsort
            rgb_input = PixelSortInput("RGB", rgb=True)
            # NOTE keeping pixelsort_input as a list so I can do 'for ... in pixelsort_input'
            #      not sure if this is smart at all but it saves a few loc.
            self.pixelsort_input = [rgb_input]
        for widget in self.pixelsort_input:
            self.pixelsort_input_container.addWidget(widget)
    
    # NOTE: I'm not sure which class should handle the call to pixelsort.
    #       I think I'll try this way and then if it's slow I'll try the inverse.
    def performGlitch(self, source_filename):
        source_image = Image.open(source_filename)
        if self._bandsort:
            bands = []
            for band, band_input in zip(source_image.split(), self.pixelsort_input):
                band_glitch = self.band_input.performGlitch(band)
                bands.append(band_glitch)
            glitch_image = Image.merge("RGB", tuple(bands))
        else:
            glitch_image = self.pixelsort_input[0].performGlitch(source_image)
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
        self._size_hint = screen_size / 1.5
        self.default_pixmap_max_size = self.sizeHint() * 3 / 8

        self.initUI()
        self.setWindowTitle("Pixel Sorting")

    def sizeHint(self):
        return self._size_hint

    def initUI(self):
        self.main_layout = QGridLayout()

        image_select_hbox = QHBoxLayout()
        file_select_label = QLabel("Image source:")
        self.image_source_input = QLineEdit()
        self.image_source_input.editingFinished.connect(self.setImageFromLineInput)
        file_browser_button = QPushButton("Browse...")
        file_browser_button.clicked.connect(self.openFileSelect)
        self.source_image_label = QLabel("Select an image to edit")

        image_select_hbox.addWidget(file_select_label)
        image_select_hbox.addWidget(self.image_source_input)
        image_select_hbox.addWidget(file_browser_button)


        self.middle = QWidget()
        self.middle.setMinimumWidth(144)
        self.middle_layout = QVBoxLayout(self.middle)
        self.middle_layout.setAlignment(Qt.AlignCenter)

        glitch_settings_label = QLabel("Glitch Settings")

        # TODO add a control for the type of glitch to perform and make this more abstract.
        self.glitch_widget = PixelSortWidget()
        self.glitch_it_button = QPushButton("Glitch It!")
        self.glitch_it_button.setEnabled(False)
        self.glitch_it_button.clicked.connect(self.performGlitch)

        self.middle_layout.addWidget(glitch_settings_label)
        self.middle_layout.addWidget(self.glitch_widget)
        self.middle_layout.addWidget(self.glitch_it_button)

        self.middle.setLayout(self.middle_layout)

        glitch_file_hbox = QHBoxLayout()

        self.glitch_filename_label = QLabel()
        save_glitch_copy = QPushButton("Save Copy As")
        save_glitch_copy.clicked.connect(self.openSaveAs)

        glitch_file_hbox.addWidget(self.glitch_filename_label)
        glitch_file_hbox.addWidget(save_glitch_copy)
        glitch_file_hbox.setStretch(0, 3)
        glitch_file_hbox.setStretch(1, 1)

        self.glitch_image_label = QLabel("Glitch goes here!")
        self.enlarge_glitch_image = QPushButton("Enlarge")
        self.enlarge_glitch_image.clicked.connect(lambda _: self.openImageInNewWindow("glitch"))
        self.swap_glitch_button = QPushButton("Use as source image")
        self.swap_glitch_button.setMaximumWidth(144)
        self.swap_glitch_button.setEnabled(False)
        self.swap_glitch_button.clicked.connect(self.setGlitchAsSource)


        # Left side - source image selection
        self.main_layout.addLayout(image_select_hbox, 0, 0, Qt.AlignCenter)
        self.main_layout.addWidget(self.source_image_label, 2, 0, Qt.AlignCenter)# | Qt.AlignTop)

        self.main_layout.setColumnMinimumWidth(1, 24)

        # Middle - controls
        self.main_layout.addWidget(self.middle, 0, 2, 4, 1, Qt.AlignCenter | Qt.AlignTop)
        self.main_layout.setColumnMinimumWidth(3, 24)

        # Right side - output view / controls
        self.main_layout.addLayout(glitch_file_hbox, 0, 4)
        self.main_layout.addWidget(self.enlarge_glitch_image, 1, 4, Qt.AlignLeft)
        self.main_layout.addWidget(self.swap_glitch_button, 1, 4, Qt.AlignRight)
        self.main_layout.addWidget(self.glitch_image_label, 2, 4, Qt.AlignCenter)# | Qt.AlignTop)

        self.main_layout.setRowStretch(1, 3)

        self.main_layout.setColumnStretch(0, 3)
        self.main_layout.setColumnStretch(2, 1)
        self.main_layout.setColumnStretch(4, 3)

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
        self.source_pixmap = QPixmap(self.source_filename)
        self.source_pixmap = self.source_pixmap.scaled(self.source_pixmap.size().boundedTo(self.getMaxImageSize()), Qt.KeepAspectRatio)
        self.source_image_label.setPixmap(self.source_pixmap)
        self.glitch_it_button.setEnabled(True)
        #self.source_image = Image.open(filename)

    # NOTE
    # For some reason using PIL.ImageQt to convert the PIL.Image.Image to a PyQt5.QtGui.QImage and then
    # using PyQt5.QtGui.QPixmap.fromImage causes the pixmap to be translucent
    # So for now I don't do that. Instead I just load the pixmap using the filename
    def setGlitchImage(self, pil_image):
        self.glitch_qimage = ImageQt(pil_image)
        self.glitch_filename = pil_image.filename
        self.glitch_filename_label.setText(f'Glitch Path: {self.glitch_filename}')
        #self.glitch_pixmap = QPixmap.fromImage(self.glitch_qimage, Qt.NoFormatConversion)
        self.glitch_pixmap = QPixmap(self.glitch_filename)
        self.glitch_pixmap = self.glitch_pixmap.scaled(self.glitch_pixmap.size().boundedTo(self.getMaxImageSize()), Qt.KeepAspectRatio)
        self.glitch_image_label.setPixmap(self.glitch_pixmap)
        self.swap_glitch_button.setEnabled(True)

    def setGlitchAsSource(self):
        self.setSourceImage(self.glitch_filename)

    def saveGlitchCopy(self, file_destination):
        self.glitch_qimage.save(file_destination)

    def performGlitch(self):
        if self.glitch_filename and not (self.glitch_filename == self.source_filename):
            # NOTE : improve file deletion and stuff
            self.deleteImage(self.glitch_filename)
        glitch_image = self.glitch_widget.performGlitch(self.source_filename)
        util.make_temp_file(glitch_image, self.default_path)
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
