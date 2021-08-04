""" imagewidget - working on a widget to contain the images in glitchart-qt """
# Copyright (c) 2021 Mark Schloeman

from PySide6.QtWidgets import QLabel, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QGraphicsScene, QGraphicsView, QSizePolicy
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, Signal



class ScrollableImageViewer(QWidget):
    def __init__(self, filename=None, metadata=None):
        super().__init__()
        self.loadUI()
        self.scene_pixmap = None
        if filename:
            self.setImage(filename)
        else:
            self.image_info_label.setText("No Image :/")

    def loadUI(self):
        self.layout = QVBoxLayout(self)

        min_zoom = 0.1
        max_zoom = 8.0

        self.scene = QGraphicsScene()
        self.view = ZoomableGraphicsView(1.0, min_zoom, max_zoom, self.scene)
        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding))

        self.info_bar = QHBoxLayout()
        self.image_info_label = QLabel()
        self.zoom_label = QLabel()
        self.zoom_label.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Maximum))
        self.zoom_slider = QSlider()
        self.zoom_slider.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Maximum))
        self.zoom_slider.setOrientation(Qt.Horizontal)
        self.zoom_slider.setMinimum(min_zoom * 100)
        self.zoom_slider.setMaximum(max_zoom * 100)
        self.info_bar.addWidget(self.image_info_label, Qt.AlignLeft)
        self.info_bar.addWidget(self.zoom_label, Qt.AlignRight)
        self.info_bar.addWidget(self.zoom_slider, Qt.AlignRight)
        self.info_bar.setAlignment(Qt.AlignRight)

        # NOTE the signals have to be kind of weird to prevent
        #       back and forth calls between this and ZoomableGraphicsView
        self.zoom_slider.sliderReleased.connect(self.setViewZoom)
        self.zoom_slider.valueChanged.connect(lambda v: self.zoom_label.setText(f'{str(v):>3}%'))
        self.view.zoomChanged.connect(self.syncSlider)

        self.zoom_slider.setValue(100)

        self.layout.addWidget(self.view)
        self.layout.addLayout(self.info_bar)

    def setViewZoom(self):
        self.view.setZoom(self.zoom_slider.value() / 100)

    def syncSlider(self, new_zoom):
        self.zoom_slider.setValue(new_zoom * 100)

    def setImage(self, filename):
        self.scene.clear()
        self.source_pixmap = QPixmap(filename) # I don't know why I have two pixmaps. It's from a long time ago so...
        self.scene_pixmap = self.source_pixmap
        self.scene.setSceneRect(self.scene_pixmap.rect()) # Prevents the scroll area from growing after each image
        self.scene.addPixmap(self.scene_pixmap)

        image_size = self.source_pixmap.size()
        self.image_info_label.setText(f'{filename} | {image_size.width()}x{image_size.height()}')

        self.resetView()

    def resetView(self, center=True):
        self.syncSlider(1.0)
        self.setViewZoom()
        self.view.fitInView(self.scene_pixmap.rect(), Qt.KeepAspectRatio)
        self.view.centerOn(self.scene.items()[0])

    def resizeEvent(self, event):
        # When the widget changes size I want to update the size of the image.
        # When the widget grows the image takes up the same relative space.
        zoom = self.zoom_slider.value() / 100
        self.resetView()
        self.syncSlider(zoom)
        self.setViewZoom()



# NOTE I don't know much about the QTransform matrix but it might be able to make the scaling simpler.
# NOTE The GraphicsView.scale method scales relative to the current viewed size but my slider in ScrollableImageViewer
#      displays the scale relative to the original image's size.
#      Because of this I need to switch back and forth between relative and absolute scaling.
#      That's why ZoomableGraphicsView has an additional property, zoom_level, which maintains the total product of
#      every scale applied.
class ZoomableGraphicsView(QGraphicsView):
    zoomChanged = Signal(float) # Emits the new scaling factor relative to the original image size

    def __init__(self, zoom, min_zoom, max_zoom, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.zoom_level = zoom
        self.min_zoom = min_zoom
        self.max_zoom = max_zoom

    def setZoom(self, new_zoom):
        # NOTE this returns zoom_level so the parent widget knows if the zoom was limited by min_zoom
        new_zoom = min(self.max_zoom, max(new_zoom, self.min_zoom))
        scale = (1.0 / self.zoom_level) * new_zoom
        self.scale(scale, scale)
        self.zoom_level = new_zoom
        return self.zoom_level

    def incrementZoom(self, zoom_delta):
        if self.max_zoom < self.zoom_level * zoom_delta or self.zoom_level * zoom_delta < self.min_zoom:
            return None
        self.scale(zoom_delta, zoom_delta)
        self.zoom_level *= zoom_delta
        self.zoomChanged.emit(self.zoom_level)

    def wheelEvent(self, event):
        zoom_delta = 1.0 + (event.angleDelta().y() / 8.0 / 360.0)
        self.incrementZoom(zoom_delta)


def main():
    from PySide6.QtWidgets import QApplication, QPushButton
    import sys
    app = QApplication([])
    filename = "/home/mark/data/pictures/glitch/input/banquet.jpg"
    filename2 = "/home/mark/data/pictures/glitch/input/dolomes.jpg"
    w = QWidget()
    l = QVBoxLayout(w)
    i = ScrollableImageViewer(filename)
    b = QPushButton("Change")
    b.clicked.connect(lambda x: i.setImage(filename2))
    l.addWidget(i)
    l.addWidget(b)
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
