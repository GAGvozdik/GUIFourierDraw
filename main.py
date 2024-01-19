import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QFileDialog, QVBoxLayout, QWidget
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainterPath
from scipy import interpolate
import numpy as np
from scipy.interpolate import CubicSpline
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import *
from scipy.interpolate import splrep, splev
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QMainWindow, QVBoxLayout, QWidget, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QProgressBar
from PyQt5.QtCore import QThread, pyqtSignal
import matplotlib.animation as animation
from matplotlib.patches import FancyArrowPatch
from PyQt5.QtCore import QTimer

# TODO make choose del points
# TODO качество gif плохое
# TODO стили сделай
# TODO размер стрелок

# TODO подпиши программу сверху
# TODO раздели по потокам
# TODO добавь try except везде где можно
# TODO ставить точки без картинки
# TODO при наведении на точку меняй ее цвет и позволяй перетащить
# TODO проверь все кнопки на вылеты
# TODO



class PhotoViewer(QtWidgets.QGraphicsView):
    photoClicked = QtCore.pyqtSignal(QtCore.QPoint)
    def __init__(self, parent):
        super(PhotoViewer, self).__init__(parent)

        self._zoom = 0
        self._empty = True
        self._scene = QtWidgets.QGraphicsScene(self)
        # self._scene.setSceneRect(0, 0, 700, 400)  # Задаем фиксированный размер
        self._photo = QtWidgets.QGraphicsPixmapItem()
        self._photo.setCursor(QtCore.Qt.ArrowCursor)
        self._scene.addItem(self._photo)
        self.setScene(self._scene)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(255, 255, 255)))
        self.setFrameShape(QtWidgets.QFrame.NoFrame)

        self.finallist = []
        self.points = []
        self.r = 5
        self.pixmap = None
        # self._scene.setCursor(QtCore.Qt.ArrowCursor)


    def hasPhoto(self):
        return not self._empty

    def fitInView(self, scale=True):
        rect = QtCore.QRectF(self._photo.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if self.hasPhoto():
                unity = self.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
                viewrect = self.viewport().rect()
                scenerect = self.transform().mapRect(rect)
                factor = min(viewrect.width() / scenerect.width(),
                             viewrect.height() / scenerect.height())
                self.scale(factor, factor)
            self._zoom = 0
        QtWidgets.QApplication.restoreOverrideCursor()

    def setPhoto(self, pixmap=None):
        items = self._scene.items()  # Получаем список всех элементов на сцене

        for i in range(len(items)):
            if isinstance(items[i], QtWidgets.QGraphicsEllipseItem):  # Проверяем, является ли элемент точкой (ellipse)
                self._scene.removeItem(items[i])  # Удаляем только точки из сцены
        self.points = []
        self._zoom = 0

        self.pixmap = pixmap
        if pixmap and not pixmap.isNull():
            self._empty = False
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
            self._photo.setPixmap(pixmap)
        else:
            self._empty = True
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            self._photo.setPixmap(QtGui.QPixmap())
        self.fitInView()

    def wheelEvent(self, event):
        if self.hasPhoto():
            if event.angleDelta().y() > 0:
                factor = 1.25
                self._zoom += 1
            else:
                factor = 0.8
                self._zoom -= 1
            if self._zoom > 0:
                self.scale(factor, factor)
            elif self._zoom == 0:
                self.fitInView()
            else:
                self._zoom = 0

    def plotOnPicture(self):
        if len(self.points) > 10:
            self.spline(self.points)
            # print(self.spline(self.points))


            for i in range(len(self.finallist) - 1):
                line = QGraphicsLineItem(
                    self.finallist[i][0],
                    self.finallist[i][1],
                    self.finallist[i + 1][0],
                    self.finallist[i + 1][1])
                pen = QtGui.QPen(QtCore.Qt.black, self.r / 2, Qt.SolidLine)
                line.setPen(pen)
                self.scene().addItem(line)

            line = QGraphicsLineItem(
                self.finallist[-1][0],
                self.finallist[-1][1],
                self.points[0][0],
                self.points[0][1])

            pen = QtGui.QPen(QtCore.Qt.black, self.r / 2, Qt.SolidLine)
            line.setPen(pen)
            self.scene().addItem(line)

        for point in self.points:  # Рисуем все точки, кроме последней
            x, y = point
            pen = QtGui.QPen(QtCore.Qt.red)
            brush = QtGui.QBrush(QtCore.Qt.red)
            self.scene().addEllipse(x - self.r / 2, y - self.r / 2, self.r, self.r, pen, brush)

        self.update()

    def mousePressEvent(self, event):
        viewPos = self.mapToScene(event.pos())

        if not self._empty and event.button() == QtCore.Qt.MiddleButton:
            self._lastPanPoint = event.pos()
            super(PhotoViewer, self).mousePressEvent(event)

        if event.button() == QtCore.Qt.LeftButton:


            if self.sceneRect().contains(viewPos) and (viewPos.x(), viewPos.y()) not in self.points:
                self.points.append((viewPos.x(), viewPos.y()))


            self.delSplineLine()

            self.plotOnPicture()

        if event.button() == Qt.RightButton:  # Обрабатываем нажатие правой кнопки мыши
            if len(self.points) > 0:

                self.delAllPoints()

                if len(self.points) > 1:
                    self.points.pop()  # Удаляем последнюю точку из списка

                self.delSplineLine()

                if len(self.points) > 4:
                    self.spline(self.points)
                    # print(self.spline(self.points))
                    print(self.finallist)
                    for i in range(len(self.finallist) - 1):
                        line = QGraphicsLineItem(
                            self.finallist[i][0],
                            self.finallist[i][1],
                            self.finallist[i + 1][0],
                            self.finallist[i + 1][1])
                        pen = QtGui.QPen(QtCore.Qt.black, self.r / 2, Qt.SolidLine)
                        line.setPen(pen)
                        self.scene().addItem(line)

                    line = QGraphicsLineItem(
                        self.finallist[-1][0],
                        self.finallist[-1][1],
                        self.points[0][0],
                        self.points[0][1])

                    pen = QtGui.QPen(QtCore.Qt.black, self.r / 2, Qt.SolidLine)
                    line.setPen(pen)
                    self.scene().addItem(line)

                for point in self.points:  # Рисуем все точки, кроме последней
                    x, y = point
                    pen = QtGui.QPen(QtCore.Qt.red)
                    brush = QtGui.QBrush(QtCore.Qt.red)
                    self.scene().addEllipse(x - self.r / 2, y - self.r / 2, self.r, self.r, pen, brush)

        # super(PhotoViewer, self).mousePressEvent(event)
        self._photo.setCursor(QtCore.Qt.ArrowCursor)

    def mouseMoveEvent(self, event):
        if not self._empty and event.buttons() == QtCore.Qt.MiddleButton:
            if not self._lastPanPoint.isNull():
                delta = event.pos() - self._lastPanPoint
                self._lastPanPoint = event.pos()
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
                self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
        else:
            self._lastPanPoint = QtCore.QPoint()
        super(PhotoViewer, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.MiddleButton:
            self._lastPanPoint = QtCore.QPoint()
        super(PhotoViewer, self).mouseReleaseEvent(event)
        self._photo.setCursor(QtCore.Qt.ArrowCursor)

    def spline(self, pointsList):

        data = np.array(pointsList)
        dts = np.linalg.norm(data[1:] - data[:-1], axis=1)
        tts = np.zeros(len(data))
        tts[1:] = np.cumsum(dts)
        smoothness = 10

        t_arr = np.linspace(0, tts[-1], len(data) * smoothness)
        xtck = splrep(tts, data[:, 0])
        ytck = splrep(tts, data[:, 1])

        xins = splev(t_arr, xtck)
        yins = splev(t_arr, ytck)

        ends_xs = np.concatenate((xins[-2:], xins[:2]))
        ends_ys = np.concatenate((yins[-2:], yins[:2]))
        ends_ts = np.array([0, 1, smoothness + 1, smoothness + 2])

        cls_xtck = splrep(ends_ts, ends_xs)
        cls_ytck = splrep(ends_ts, ends_ys)
        cls_ts = np.arange(smoothness + 3)
        cls_xs = splev(cls_ts, cls_xtck)
        cls_ys = splev(cls_ts, cls_ytck)

        finalxs = np.concatenate((xins, cls_xs[2:-2]))
        finalys = np.concatenate((yins, cls_ys[2:-2]))

        self.finallist = [(finalxs[i], finalys[i]) for i in range(len(finalxs))]

    def hidePhoto(self):
        self._photo.hide()

    def showPhoto(self):
        self._photo.show()

    def delAllPoints(self):

        items = self.scene().items()  # Получаем список всех элементов на сцене
        for item in items:  # Проходим по всем элементам сцены

            if type(item) == QGraphicsEllipseItem:  # Проверяем, является ли элемент точкой (ellipse)
                self.scene().removeItem(item)  # Удаляем только точки из сцены

    def delSplineLine(self):
        items = self.scene().items()  # Получаем список всех элементов на сцене
        for item in items:  # Проходим по всем элементам сцены
            if type(item) == QGraphicsLineItem:  # Проверяем, является ли элемент точкой (ellipse)
                self.scene().removeItem(item)


##############################################################################################
#
##############################################################################################

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setGeometry(100, 100, 1800, 400)

        layout = QVBoxLayout()

        #####################################################################################
        # debug
        #####################################################################################

        self.viewer = PhotoViewer(self)

        HBlayout = QtWidgets.QVBoxLayout()
        HBlayout.setAlignment(QtCore.Qt.AlignRight)
        HBlayout.addWidget(self.viewer)

        #####################################################################################
        #
        #####################################################################################

        self.fps = 30
        self.dpi = 100
        self.quantity = 20
        self.sums = np.array([])
        self.interval = 1
        # self.number = 5000
        self.number = 1000
        self.repeatDelay = 1

        self.images = []

        self.previewCoice = 0

        #####################################################################################
        # Panel
        #####################################################################################

        self.panel = QGroupBox()
        vbox = QVBoxLayout()
        self.panel.setLayout(vbox)

        self.load_button = QPushButton('Load image', self)
        self.load_button.clicked.connect(self.loadImage)
        vbox.addWidget(self.load_button)

        self.animButton = QPushButton('Plot animation', self)
        self.animButton.clicked.connect(self.plotAnim)
        vbox.addWidget(self.animButton)

        save_button = QPushButton('Save Animation')
        save_button.clicked.connect(self.save_animation)
        vbox.addWidget(save_button)

        loadPointsButton = QPushButton('Load points from file')
        loadPointsButton.clicked.connect(self.loadFromFile)
        vbox.addWidget(loadPointsButton)

        savePointsButton = QPushButton('Save points to file')
        savePointsButton.clicked.connect(self.save2File)
        vbox.addWidget(savePointsButton)

        previewButton = QPushButton('Preview')
        previewButton.clicked.connect(self.showPreview)

        # Добавляю полосы прокрутки
        self.arrowNumberScrollBar = QScrollBar(Qt.Horizontal)
        self.arrowNumberScrollBar.setMinimum(2)
        self.arrowNumberScrollBar.setMaximum(300)
        self.arrowNumberScrollBar.setValue(20)  # Устанавливаем начальное значение
        self.arrowNumberScrollBar.valueChanged.connect(self.chageAroowsNumber)
        self.arrowNumberScrollBar.hide()


        self.arrowLabel = QLabel("Line width", self)
        self.arrowLabel.hide()

        scrollBarGroup2 = QGroupBox()
        scrollBarBox2 = QVBoxLayout()
        scrollBarGroup2.setLayout(scrollBarBox2)

        scrollBarBox2.addWidget(previewButton)
        scrollBarBox2.addWidget(self.arrowLabel)
        scrollBarBox2.addWidget(self.arrowNumberScrollBar)

        scrollBarGroup2.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)  # устанавливаем политику размеров метки

        vbox.addWidget(scrollBarGroup2)


        # Добавляю полосы прокрутки
        self.lineWidthScrollBar = QScrollBar(Qt.Horizontal)
        self.lineWidthScrollBar.setMinimum(1)
        self.lineWidthScrollBar.setMaximum(200)
        self.lineWidthScrollBar.setValue(10)  # Устанавливаем начальное значение
        self.lineWidthScrollBar.valueChanged.connect(self.updateLineWidth)

        label = QLabel("Line width", self)

        scrollBarGroup1 = QGroupBox()
        scrollBarBox1 = QVBoxLayout()
        scrollBarGroup1.setLayout(scrollBarBox1)

        scrollBarBox1.addWidget(label)
        scrollBarBox1.addWidget(self.lineWidthScrollBar)

        scrollBarGroup1.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)  # устанавливаем политику размеров метки

        vbox.addWidget(scrollBarGroup1)

        self.isTransparent = False
        self.checkbox = QCheckBox("Transparency")
        self.checkbox.toggled.connect(self.toggleImageVisibility)
        vbox.addWidget(self.checkbox)


        #####################################################################################
        # Window
        #####################################################################################

        window = QGroupBox()
        vbox = QHBoxLayout()
        window.setLayout(vbox)

        self.figure = plt.figure(dpi=self.dpi)
        self.ax1 = self.figure.add_subplot()
        self.ax1.set_axis_off()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setFixedSize(800, 800)
        vbox.addWidget(self.canvas)


        vbox.addLayout(HBlayout)
        # vbox.addLayout(self.viewer)

        vbox.addWidget(self.panel)


        layout.addWidget(window)


        self.progress = QProgressBar(self)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        layout.addWidget(self.progress)
        self.hideProgressBar()

        #####################################################################################
        #
        #####################################################################################

        self.setLayout(layout)

        self.file_name = None


    def chageAroowsNumber(self, n):
        self.quantity = n
        self.showPreview()



    def showPreview(self):

        if len(self.viewer.points) < 5:
            print('fuck')
            return


        self.arrowNumberScrollBar.show()
        self.arrowLabel.show()

        # self.ax1.clear()


        if self.previewCoice != 0:

            print('You')
            self.animS.event_source.stop()
            self.ax1.clear()
            self.ax1.set_aspect(1)
            self.ax1.set_axis_off()

        else:
            self.ax1.clear()
            self.ax1.set_aspect(1)
            self.ax1.set_axis_off()

        self.calcTrace()

        test = np.sum(np.array(
            [self.cns[i + self.quantity] * np.exp(-1j * i * self.phis) for i in range(-self.quantity, self.quantity + 1)]), axis=0)

        self.ax1.plot(np.real(test), np.imag(test), c='lightgrey', linewidth='1.0')


        phi = 0

        arrows = np.zeros((2 * self.quantity + 1, 2))
        z = self.cns[self.quantity]
        arrows[0] = z.real, z.imag

        for i in range(1, self.quantity):

            z = self.cns[self.quantity + i] * np.exp(1j * i * phi)
            arrows[2 * i - 1] = z.real, z.imag

            z = self.cns[self.quantity - i] * np.exp(-1j * i * phi)
            arrows[2 * i] = z.real, z.imag

        sums = np.zeros_like(arrows)
        sums[0] = arrows[0]

        for i in range(1, 2 * self.quantity + 1):
            sums[i] = sums[i - 1] + arrows[i]

        # self.ax1.plot(sums[:, 0], sums[:, 1], c='black', linewidth='1.0')

        self.head_width = 10
        self.head_length = 5

        for i in range(len(sums) - 1):
            self.ax1.arrow(
                sums[:, 0][i],
                sums[:, 1][i],
                sums[:, 0][i + 1] - sums[:, 0][i],
                sums[:, 1][i + 1] - sums[:, 1][i],
                color='black',
                head_width=self.head_width,
                head_length=self.head_length,
                length_includes_head = True
            )

            self.head_width -= self.head_width / (len(sums) + 1)
            self.head_length -= self.head_width / (len(sums) + 1)
            # pass


        self.canvas.figure = self.figure
        self.canvas.draw()






    def updateLineWidth(self, r):
        self.viewer.r = r / 10
        self.viewer.delSplineLine()
        self.viewer.delAllPoints()
        self.viewer.plotOnPicture()

    def toggleImageVisibility(self, state):
        # self.image_label.setGraphicsEffect(QGraphicsOpacityEffect(opacity=opacity))
        if self.isTransparent == False:
            self.isTransparent = True
            self.viewer.hidePhoto()
        else:
            self.isTransparent = False
            self.viewer.showPhoto()

    def loadImage(self):


        self.viewer.points = []
        self.viewer.delSplineLine()
        self.viewer.delAllPoints()
        self.viewer.update()

        self.viewer.points = []
        options = QFileDialog.Options()
        self.file_name, _ = QFileDialog.getOpenFileName(self, "Выберите изображение", "", "Изображения (*.png *.jpg *.jpeg *.bmp *.gif)", options=options)

        if self.file_name != None:
            self.viewer.setPhoto(QtGui.QPixmap(self.file_name))

    def stopAnim(self):

        # self.ax1.clear()


        self.animS = None


        self.ax1.clear()

        # self.plotGraph()
        pass

    def calcTrace(self):

        x = []
        y = []

        finallist = self.viewer.finallist

        for i in range(len(finallist)):
            # pass
            x.append(finallist[i][0])
            y.append(-finallist[i][1])

        x.append(self.viewer.points[0][0])
        y.append(-self.viewer.points[0][1])


        spline_points = self.viewer.finallist

        self.phis = np.linspace(0, 2 * np.pi, len(spline_points) + 1)[:-1]

        res = np.array([gg[0] for gg in spline_points])
        ims = np.array([-gg[1] for gg in spline_points])

        def cn(n, res, ims):
            exparr = np.exp(-1j * n * self.phis)
            return (np.dot(exparr, res) + 1j * np.dot(exparr, ims)) / len(spline_points)

        self.cns = np.array([cn(i, res, ims) for i in range(-self.quantity, self.quantity + 1)])

    def plotAnim(self):
        self.previewCoice += 1
        self.panel.hide()
        self.arrowNumberScrollBar.hide()
        self.arrowLabel.hide()

        if len(self.viewer.points) < 4:
            self.panel.show()
            return
        self.stopAnim()
        self.showProgressBar()


        if len(self.viewer.points) > 3:

            self.ax1.set_aspect(1)
            self.ax1.set_axis_off()

        self.calcTrace()

        test = np.sum(np.array(
            [self.cns[i + self.quantity] * np.exp(-1j * i * self.phis) for i in range(-self.quantity, self.quantity + 1)]), axis=0)

        contour, = self.ax1.plot(np.real(test), np.imag(test), c='lightgrey', linewidth='7.0')

        traceX = []
        traceY = []

        self.images = []

        for phi in np.linspace(0, 2 * np.pi, self.number)[:-1]:

            arrows = np.zeros((2 * self.quantity + 1, 2))
            z = self.cns[self.quantity]
            arrows[0] = z.real, z.imag

            for i in range(1, self.quantity):

                z = self.cns[self.quantity + i] * np.exp(1j * i * phi)
                arrows[2 * i - 1] = z.real, z.imag

                z = self.cns[self.quantity - i] * np.exp(-1j * i * phi)
                arrows[2 * i] = z.real, z.imag

            sums = np.zeros_like(arrows)
            sums[0] = arrows[0]

            for i in range(1, 2 * self.quantity + 1):
                sums[i] = sums[i - 1] + arrows[i]

            traceX.append(sums[-1][0])
            traceY.append(sums[-1][1])
            trace, = self.ax1.plot(traceX, traceY, c='grey', linewidth='0.7', animated=True)



            # image, = plt.plot(sums[:, 0], sums[:, 1], c='black', linewidth='1.0', animated=True)

            self.images.append([contour, trace])
            # self.images.append([trace])

            self.head_width = 5
            self.head_length = 5

            for i in range(len(sums) - 1):
                self.images[-1].append(self.ax1.arrow(
                    sums[:, 0][i],
                    sums[:, 1][i],
                    -sums[:, 0][i] + sums[:, 0][i + 1],
                    -sums[:, 1][i] + sums[:, 1][i + 1],
                    color='black',
                    head_width=self.head_width,
                    head_length=self.head_length,
                    length_includes_head=True
                ))

                self.head_width -= self.head_width / (len(sums) + 1)
                self.head_length -= self.head_width / (len(sums) + 1)
                # pass



            self.progress.setValue(int(10 * phi / 2 * np.pi))

        self.progress.setValue(100)
        self.hideProgressBar()

        anim = animation.ArtistAnimation(self.figure, self.images, interval=self.interval, blit=True, repeat_delay=self.repeatDelay)

        self.animS = anim

        self.panel.show()


    def save_animation(self):

        self.panel.hide()

        self.showProgressBar()
        file_dialog = QFileDialog.getSaveFileName(self, 'Save Animation', '', 'GIF Files (*.gif)')
        file_path = file_dialog[0]
        if file_path:

            writer = animation.PillowWriter(fps=self.fps)
            self.animS.save(file_path, writer=writer, progress_callback=self.update_progress)

        self.progress.setValue(100)
        self.hideProgressBar()

        self.panel.show()

    def update_progress(self, i, n):

        progress = int(( i / (2 * self.number)) * 100)
        print(i)

        self.progress.setValue(progress)

    def save2File(self):

        file_dialog = QFileDialog.getSaveFileName(self, 'Save points to file', '', 'txt Files (*.txt)')
        file_path = file_dialog[0]
        if file_path:
            file = open(file_path, 'w')
            for point in self.viewer.points:
                line = str(point[0]) + ', ' + str(point[1]) + '\n'
                file.write(line)
            file.close()

    def loadFromFile(self):


        self.viewer.delAllPoints()
        self.viewer.delSplineLine()

        if self.previewCoice != 0:
            self.animS.event_source.stop()
            self.ax1.clear()
            self.ax1.set_aspect(1)
            self.ax1.set_axis_off()


        options = QFileDialog.Options()
        file_name = QFileDialog.getOpenFileName(self, "Выберите файл с точками", "", "Точки (*.txt)", options=options)
        if file_name:
            file = open(file_name[0], 'r')

            for line in file:
                self.viewer.points.append((float(line.split(',')[0]), float(line.split(',')[1])))
            file.close()



        self.viewer.update()

        # self.ax1.set_xlim(np.array(self.viewer.points)[:, 0].min(), np.array(self.viewer.points)[:, 0].max())
        # self.ax1.set_ylim(np.array(self.viewer.points)[:, 1].min(), np.array(self.viewer.points)[:, 1].max())

        self.viewer.delSplineLine()
        self.viewer.plotOnPicture()

        if len(self.viewer.points) > 3:
            # self.figure.clear()
            # self.ax1 = self.figure.add_subplot()
            # self.ax1.set_axis_off()
            # self.ax1.set_aspect(1)
            #
            # self.canvas.figure = self.figure
            # self.canvas.draw()
            self.animS=None
            pass

        self.viewer.update()

    def hideProgressBar(self):
        self.progress.hide()

    def showProgressBar(self):
        self.progress.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())










