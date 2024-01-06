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
from PyQt5.QtGui import QColor, QPen
from PyQt5.QtCore import Qt

import matplotlib.animation as animation
from matplotlib.patches import FancyArrowPatch


# TODO make choose del points

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
        self.r = 0.5
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

    def mousePressEvent(self, event):
        viewPos = self.mapToScene(event.pos())

        if not self._empty and event.button() == QtCore.Qt.MiddleButton:
            self._lastPanPoint = event.pos()
            super(PhotoViewer, self).mousePressEvent(event)

        if event.button() == QtCore.Qt.LeftButton:


            if self.sceneRect().contains(viewPos) and (viewPos.x(), viewPos.y()) not in self.points:
                self.points.append((viewPos.x(), viewPos.y()))


            self.delSplineLine()

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

            # if self.sceneRect().contains(viewPos) and (viewPos.x(), viewPos.y()) not in self.points:
            #     x, y = self.points[-1]
            #     pen = QtGui.QPen(QtCore.Qt.red)
            #     brush = QtGui.QBrush(QtCore.Qt.red)
            #     self.scene().addEllipse(x - int(self.r / 2), int(y - self.r / 2), self.r, self.r, pen, brush)
            for point in self.points:  # Рисуем все точки, кроме последней
                x, y = point
                pen = QtGui.QPen(QtCore.Qt.red)
                brush = QtGui.QBrush(QtCore.Qt.red)
                self.scene().addEllipse(x - int(self.r / 2), int(y - self.r / 2), self.r, self.r, pen, brush)

        self.update()

        if event.button() == Qt.RightButton:  # Обрабатываем нажатие правой кнопки мыши
            if len(self.points) > 0:

                self.delAllPoints()

                if len(self.points) > 0:
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
                    self.scene().addEllipse(x - int(self.r / 2), int(y - self.r / 2), self.r, self.r, pen, brush)

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



        self.setGeometry(100, 100, 1400, 400)

        layout = QVBoxLayout()


        #####################################################################################
        # debug
        #####################################################################################
        self.viewer = PhotoViewer(self)

        HBlayout = QtWidgets.QVBoxLayout()
        HBlayout.setAlignment(QtCore.Qt.AlignRight)
        # HBlayout.addWidget(self.btnLoad)
        HBlayout.addWidget(self.viewer)

        #####################################################################################
        # Panel
        #####################################################################################

        panel = QGroupBox()
        vbox = QVBoxLayout()
        panel.setLayout(vbox)

        self.load_button = QPushButton('Load image', self)
        self.load_button.clicked.connect(self.loadImage)
        vbox.addWidget(self.load_button)

        # self.plot_button = QPushButton('Plot graph', self)
        # self.plot_button.clicked.connect(self.plotGraph)
        # vbox.addWidget(self.plot_button)

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

        self.figure = plt.figure()
        self.ax1 = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setFixedSize(600, 600)
        vbox.addWidget(self.canvas)

        vbox.addLayout(HBlayout)
        # vbox.addLayout(self.viewer)

        vbox.addWidget(panel)
        layout.addWidget(window)

        #####################################################################################
        #
        #####################################################################################

        self.quantity = 50
        self.sums = np.array([])
        # self.arrows = [FancyArrowPatch((0, 0), (1, 1), mutation_scale=8, color='black') for _ in
        #                range(2 * self.quantity + 1)]
        self.interval = 0.1
        self.number = 5000

        #####################################################################################
        #
        #####################################################################################

        self.setLayout(layout)

        self.file_name = None


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

    #
    # def plotGraph(self):
    #
    #     self.stopAnim()
    #
    #     # self.arrows = []
    #     # for i in range(2 * self.quantity + 1):
    #     #     self.ax1.add_patch(FancyArrowPatch((0, 0), (200, -201), mutation_scale=2, color='black'))
    #     #     self.arrows.append(FancyArrowPatch((0, 0), (200, -201), mutation_scale=2, color='black'))
    #
    #
    #     if len(self.viewer.points) > 3:
    #
    #         # self.ax1.clear()
    #
    #         # self.ax1.set_xlim(-2000, 2000)
    #         # self.ax1.set_ylim(-2000, 2000)
    #         # self.ax1.set_xlim(-1000, 1000)
    #         # self.ax1.set_ylim(-2000, 1000)
    #
    #         self.ax1 = self.figure.add_subplot(111)
    #
    #         self.ax1.set_xlim(0, self.viewer._scene.width())
    #         self.ax1.set_ylim(-self.viewer._scene.height(), 0)
    #
    #         # xMax = 1.1 * np.max(np.array(self.viewer.points)[:, 0])
    #         # xMin = 0.9 * np.min(np.array(self.viewer.points)[:, 0])
    #         # yMax = 0.9 * np.max(np.array(self.viewer.points)[:, 1])
    #         # yMin = 1.1 * np.min(np.array(self.viewer.points)[:, 1])
    #         #
    #         # print((yMin, yMax))
    #         # print((xMin, xMax))
    #         # self.ax1.set_xlim(xMin, xMax)
    #         # self.ax1.set_ylim(-yMax, yMin)
    #         self.ax1.set_aspect(1)
    #
    #         x = []
    #         y = []
    #
    #         finallist = self.viewer.finallist
    #
    #         for i in range(len(finallist)):
    #             # pass
    #             x.append(finallist[i][0])
    #             y.append(-finallist[i][1])
    #
    #         x.append(self.viewer.points[0][0])
    #         y.append(-self.viewer.points[0][1])
    #
    #
    #         self.ax1.plot(np.array(x), np.array(y))
    #
    #         self.canvas.figure = self.figure
    #         self.canvas.draw()



    def stopAnim(self):

        # self.ax1.clear()

        self.figure.clear()
        self.animS = None

        # self.ax1.clear()
        # self.plotGraph()


    def plotAnim(self):
        self.stopAnim()

        # self.arrows = []
        # for i in range(2 * self.quantity + 1):
        #     self.ax1.add_patch(FancyArrowPatch((0, 0), (200, -201), mutation_scale=2, color='black'))
        #     self.arrows.append(FancyArrowPatch((0, 0), (200, -201), mutation_scale=2, color='black'))


        if len(self.viewer.points) > 3:

            # self.ax1.clear()

            # self.ax1.set_xlim(-2000, 2000)
            # self.ax1.set_ylim(-2000, 2000)
            # self.ax1.set_xlim(-1000, 1000)
            # self.ax1.set_ylim(-2000, 1000)

            self.ax1 = self.figure.add_subplot(111)

            # self.ax1.set_xlim(0, self.viewer._scene.width())
            # self.ax1.set_ylim(-self.viewer._scene.height(), 0)

            # xMax = 1.0 * np.max(self.viewer.finallist[:, 0])
            # xMin = 1.0 * np.min(self.viewer.finallist[:, 0])
            # yMax = 1.0 * np.max(self.viewer.finallist[:, 1])
            # yMin = 1.0 * np.min(self.viewer.finallist[:, 1])

            # print((xMin, xMax))
            # print((yMin, yMax))
            #
            # self.ax1.set_xlim(xMin, xMax)
            # self.ax1.set_ylim(-yMax, yMin)
            self.ax1.set_aspect(1)

            x = []
            y = []

            finallist = self.viewer.finallist

            for i in range(len(finallist)):
                # pass
                x.append(finallist[i][0])
                y.append(-finallist[i][1])

            x.append(self.viewer.points[0][0])
            y.append(-self.viewer.points[0][1])


            self.ax1.plot(np.array(x), np.array(y))

            self.canvas.figure = self.figure
            self.canvas.draw()

        if len(self.viewer.points) < 10:
            print('error')
            return
        # self.figure.clear()
        # self.plotGraph()

        spline_points = self.viewer.finallist

        #####################################################################
        #####################################################################
        #####################################################################

        phis = np.linspace(0, 2 * np.pi, len(spline_points) + 1)[:-1]

        res = np.array([gg[0] for gg in spline_points])
        ims = np.array([-gg[1] for gg in spline_points])

        def cn(n, res, ims):
            exparr = np.exp(-1j * n * phis)
            return (np.dot(exparr, res) + 1j * np.dot(exparr, ims)) / len(spline_points)

        self.cns = np.array([cn(i, res, ims) for i in range(-self.quantity, self.quantity + 1)])

        #
        # self.anim = animation.FuncAnimation(
        #     self.figure,
        #     self.update,
        #     frames=np.linspace(0, 2 * np.pi, 55),
        #     interval=0.01)
        #
        # self.anim.event_source.start()

        #####################################################################
        #####################################################################
        #####################################################################


        images = []

        # self.ax1.plot(np.real(test), np.imag(test), c='grey', linewidth='1.0')

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

            image, = plt.plot(sums[:, 0], sums[:, 1], c='black', linewidth='1.0', animated=True)
            images.append([image])

        anim = animation.ArtistAnimation(self.figure, images, interval=self.interval, blit=True, repeat_delay=1)

        self.animS = anim

        #####################################################################
        #####################################################################
        #####################################################################

        # self.canvas.figure = self.figure
        # self.canvas.draw()

    def update(self, frames):
        phi = np.linspace(0, 2 * np.pi, 1001)[:-1]

        arrows = np.zeros((2 * self.quantity + 1, 2))
        z = self.cns[self.quantity]
        arrows[0] = z.real, z.imag
        for i in range(1, self.quantity):
            z = self.cns[self.quantity + i] * np.exp(1j * i * frames)
            arrows[2 * i - 1] = z.real, z.imag
            z = self.cns[self.quantity - i] * np.exp(-1j * i * frames)
            arrows[2 * i] = z.real, z.imag

        sums = np.zeros_like(arrows)
        sums[0] = arrows[0]

        for i in range(1, 2 * self.quantity + 1):
            sums[i] = sums[i - 1] + arrows[i]

        for i in range(len(self.sums) - 1):
            self.arrows[i].set_positions((self.sums[i][0], self.sums[i][1]), (self.sums[i + 1][0], self.sums[i + 1][1]))

        return self.arrows


    def save_animation(self):
        file_dialog = QFileDialog.getSaveFileName(self, 'Save Animation', '', 'GIF Files (*.gif)')
        file_path = file_dialog[0]
        if file_path:
            writer = animation.PillowWriter(fps=30)
            self.animS.save(file_path, writer=writer)

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
        self.viewer.points = []
        self.viewer.delSplineLine()

        options = QFileDialog.Options()
        file_name = QFileDialog.getOpenFileName(self, "Выберите файл с точками", "", "Точки (*.txt)", options=options)
        print(file_name)
        if file_name:
            file = open(file_name[0], 'r')

            for line in file:
                self.viewer.points.append((float(line.split(',')[0]), float(line.split(',')[1])))
            file.close()



        self.viewer.update()

        # self.ax1.set_xlim(np.array(self.viewer.points)[:, 0].min(), np.array(self.viewer.points)[:, 0].max())
        # self.ax1.set_ylim(np.array(self.viewer.points)[:, 1].min(), np.array(self.viewer.points)[:, 1].max())

        for point in self.viewer.points:  # Рисуем все точки, кроме последней
            x, y = point
            pen = QtGui.QPen(QtCore.Qt.red)
            brush = QtGui.QBrush(QtCore.Qt.red)
            self.viewer.scene().addEllipse(x - int(self.viewer.r / 2), int(y - self.viewer.r / 2), self.viewer.r, self.viewer.r, pen, brush)


        if len(self.viewer.points) > 3:
            self.figure.clear()
            self.ax1 = self.figure.add_subplot(111)
            # self.ax1.set_aspect(1)

            x = []
            y = []
            self.viewer.spline(self.viewer.points)
            finallist = self.viewer.finallist

            for i in range(len(finallist)):
                # pass
                x.append(finallist[i][0])
                y.append(-finallist[i][1])

            x.append(self.viewer.points[0][0])
            y.append(-self.viewer.points[0][1])


            self.ax1.plot(np.array(x), np.array(y))

            self.canvas.figure = self.figure
            self.canvas.draw()

        self.viewer.update()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())










