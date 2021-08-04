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
            self.setImage(filename, metadata)
        else:
            self.image_info_label.setText("No Image :/")

    def loadUI(self):
        self.layout = QVBoxLayout(self)


        self.scene = QGraphicsScene()
        self.view = ZoomableGraphicsView(1.0, 0.1, self.scene)
        self.view.zoomChanged.connect(self.updateZoomWidget)
        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding))

        self.info_bar = QHBoxLayout()

        self.image_info_label = QLabel()
        self.zoom_label = QLabel("100%")
        self.zoom_label.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Maximum))
        self.zoom_slider = QSlider()
        self.zoom_slider.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Maximum))
        self.zoom_slider.setOrientation(Qt.Horizontal)
        self.zoom_slider.setMinimum(-90)
        self.zoom_slider.setMaximum(400)
        self.zoom_slider.sliderReleased.connect(self.updateZoom)
        self.zoom_slider.valueChanged.connect(lambda v: self.zoom_label.setText(f'{str(v + 100):>3}%'))
        self.zoom_slider.setValue(0)
        self.info_bar.addWidget(self.image_info_label, Qt.AlignLeft)
        self.info_bar.addWidget(self.zoom_label, Qt.AlignRight)
        self.info_bar.addWidget(self.zoom_slider, Qt.AlignRight)
        self.info_bar.setAlignment(Qt.AlignRight)

        self.layout.addWidget(self.view)
        self.layout.addLayout(self.info_bar)

    def updateZoom(self):
        value = self.zoom_slider.value() + 100
        self.zoom_label.setText(str(value) + "%")
        self.view.setZoom(value / 100)
        #self.view.centerOn(self.scene)

    def updateZoomWidget(self, new_zoom):
        zoom = (new_zoom - 1.0) * 100
        self.zoom_slider.setValue(zoom)

    # TODO add code here that sets the zoom level to the largest level that shows the whole image.
    #      since it might be less than 1.0 for large images or small windows.
    def setImage(self, filename, metadata=None):
        # NOTE I'm not sure why I have two identical pixmaps. I wrote this a long time ago so it could be a mistake
        #      but it might be related to the way GraphicsViews use pixmaps..?
        self.source_pixmap = QPixmap(filename)
        self.scene_pixmap = self.source_pixmap
        bounds = self.view.rect().size()
        image_size = self.source_pixmap.size()
        image_info = filename
        if metadata:
            image_info += f' | {metadata}'
        self.image_info_label.setText(image_info)
        self.updateView()

    def updateView(self, center=True):
        if self.scene_pixmap is None:
            return
        self.scene.clear()
        # NOTE I have to do this to reset the scene's rect
        # to prevent the ScrollArea from growing after changing the image a lot.
        self.scene.setSceneRect(self.scene_pixmap.rect())
        self.scene.addPixmap(self.scene_pixmap)
        self.view.fitInView(self.scene_pixmap.rect(), Qt.KeepAspectRatio)
        if center:
            self.view.centerOn(self.scene.items()[0])

    def resizeEvent(self, event):
        self.updateView()


class ZoomableGraphicsView(QGraphicsView):
    zoomChanged = Signal(float)

    def __init__(self, zoom, min_zoom, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.zoom_level = zoom
        self.min_zoom = min_zoom

    def setZoom(self, new_zoom):
        # scale is the value you need to scale the pixmap by to get it from it's current scale to the given scale
        # this value is different from new_zoom, which is the desired scale relative to the original scale
        new_zoom = max(new_zoom, self.min_zoom)
        scale = (1.0 / self.zoom_level) * new_zoom
        self.zoom_level = new_zoom
        self.scale(scale, scale)
        return self.zoom_level


    def wheelEvent(self, event):
        zoom_delta = event.angleDelta().y() / 8.0 / 360.0
        zoom_value = 1.0 + zoom_delta
        if self.zoom_level * zoom_value < self.min_zoom:
            return None
        self.zoom_level *= zoom_value
        self.scale(zoom_value, zoom_value)
        self.zoomChanged.emit(self.zoom_level)


def main():
    from PySide6.QtWidgets import QApplication
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
