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


import matplotlib.animation as animation


class ImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.transparent = False
        self.setMouseTracking(True)
        self.points = []

        self.painter = QPainter(self)

        self.r = 5.0

        self.activePoint = (1, 1)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            x = event.pos().x()
            y = event.pos().y()

            if len(self.points) < 2:
                self.points.append((x, y))
            else:
                if self.points[-1] != (x, y):
                    self.points.append((x, y))

        if event.button() == Qt.RightButton:
                self.points = self.points[:-1]
        self.update()

    # TODO make choose del points

    def mouseEvent(self, event):

        for point in self.points:
            dx = event.pos().x() - point[0]
            dy = event.pos().y() - point[1]

            if (dx * dx) / (self.r * self.r) + (dy * dy) / (self.r * self.r) <= 1:
                self.activePoint = point
                print('ggg')
            else:
                print('ggg111')
        #
        # if point != self.activePoint:
        #     painter.drawEllipse(x - int(self.r / 2), int(y - self.r / 2), self.r, self.r)
        # else:
        #     painter.end()
        #
        #     painter = QPainter(self)
        #     painter.setRenderHint(QPainter.Antialiasing)
        #     painter.setPen(QPen(Qt.green, 5, Qt.SolidLine))
        #     painter.drawEllipse(x - int(self.r / 2), int(y - self.r / 2), self.r * 4, self.r * 4)
        #
        #     painter.end()
        #     painter = QPainter(self)
        #     painter.setRenderHint(QPainter.Antialiasing)
        #     painter.setPen(QPen(Qt.black, float(self.r) / 3, Qt.SolidLine))

    #####################################################################################
    #
    #####################################################################################
    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(Qt.black, float(self.r) / 3, Qt.SolidLine))

        for point in self.points:
            x, y = point
            painter.drawEllipse(x - int(self.r / 2), int(y - self.r / 2), self.r, self.r)



        if len(self.points) > 3:

            finallist = self.spline()

            for i in range(len(finallist) - 1):
                x1, y1 = finallist[i]
                x2, y2 = finallist[i + 1]

                painter.drawLine(x1, -y1, x2, -y2)

            painter.drawLine(
                finallist[-1][0],
                -finallist[-1][1],
                self.points[0][0],
                self.points[0][1]
            )


    #####################################################################################
    #
    #####################################################################################
    def spline(self):
        data = np.array(self.points)
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

        finallist = [[finalxs[i], -finalys[i]] for i in range(len(finalxs))]
        return finallist


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.image_label = ImageLabel(self)
        self.setGeometry(100, 100, 400, 400)

        layout = QVBoxLayout()


        #####################################################################################
        # Panel
        #####################################################################################

        panel = QGroupBox()
        vbox = QHBoxLayout()
        panel.setLayout(vbox)


        self.load_button = QPushButton('Load image', self)
        self.load_button.clicked.connect(self.load_image)
        vbox.addWidget(self.load_button)

        self.plot_button = QPushButton('Plot graph', self)
        self.plot_button.clicked.connect(self.plotGraph)
        vbox.addWidget(self.plot_button)

        self.animButton = QPushButton('Plot animation', self)
        self.animButton.clicked.connect(self.plotAnim)
        vbox.addWidget(self.animButton)

        self.checkbox = QCheckBox("Transparency")
        self.checkbox.toggled.connect(self.makeTransparent)
        self.isTransparent = False
        vbox.addWidget(self.checkbox)

        layout.addWidget(panel)

        #####################################################################################
        # Window
        #####################################################################################

        window = QGroupBox()
        vbox = QHBoxLayout()
        window.setLayout(vbox)





        # self.scroll_area.alignment('AlignHCenter')
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.image_label)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFixedSize(1100, 1100)
        vbox.addWidget(self.scroll_area)

        self.figure = plt.figure()
        self.ax1 = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setFixedSize(1100, 1100)
        vbox.addWidget(self.canvas)

        layout.addWidget(window)

        #####################################################################################
        #
        #####################################################################################

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.file_name = None


    def plotGraph(self):

        self.stopAnim

        if len(self.image_label.points) > 3:
            # if event.reason() == event.Mouse:
            self.ax1.clear()


            self.ax1.set_xlim(0, self.image_label.width())
            self.ax1.set_ylim(-self.image_label.height(), 0)

            self.ax1.set_aspect(1)

            x = []
            y = []

            finallist = self.image_label.spline()

            for i in range(len(finallist)):
                # pass
                x.append(finallist[i][0])
                y.append(finallist[i][1])

            x.append(self.image_label.points[0][0])
            y.append(-self.image_label.points[0][1])


            self.ax1.plot(np.array(x), np.array(y))

            self.canvas.figure = self.figure
            self.canvas.draw()



    def stopAnim(self):
        self.figure.clear()
        self.ax1.clear()
        # self.plotGraph()


    def plotAnim(self):

        if len(self.image_label.points) < 10:
            print('error')
            return

        self.ax1.clear()
        self.plotGraph()

        spline_points = self.image_label.spline()

        #####################################################################
        #####################################################################
        #####################################################################

        phis = np.linspace(0, 2 * np.pi, len(spline_points) + 1)[:-1]

        res = np.array([gg[0] for gg in spline_points])
        ims = np.array([gg[1] for gg in spline_points])

        def cn(n, res, ims):
            exparr = np.exp(-1j * n * phis)
            return (np.dot(exparr, res) + 1j * np.dot(exparr, ims)) / len(spline_points)

        cns = np.array([cn(i, res, ims) for i in range(-100, 101)])

        test = np.sum(np.array(
            [cns[i + 100] * np.exp(-1j * i * phis) for i in range(-100, 101)]), axis=0)
        # self.ax1.plot(test.real, test.imag, c='red', linewidth=25)

        images = []

        # self.ax1.plot(np.real(test), np.imag(test), c='grey', linewidth='1.0')

        for phi in np.linspace(0, 2 * np.pi, 1001)[:-1]:
            arrows = np.zeros((201, 2))
            z = cns[100]
            arrows[0] = z.real, z.imag
            for i in range(1, 100):
                z = cns[100 + i] * np.exp(1j * i * phi)
                arrows[2 * i - 1] = z.real, z.imag
                z = cns[100 - i] * np.exp(-1j * i * phi)
                arrows[2 * i] = z.real, z.imag
            sums = np.zeros_like(arrows)
            sums[0] = arrows[0]
            for i in range(1, 201):
                sums[i] = sums[i - 1] + arrows[i]
            image, = plt.plot(sums[:, 0], sums[:, 1], c='black', linewidth='1.0', animated=True)
            images.append([image])

        anim = animation.ArtistAnimation(self.figure, images, interval=20, blit=True, repeat_delay=20)

        #####################################################################
        #####################################################################
        #####################################################################

        self.canvas.figure = self.figure
        self.canvas.draw()



    def makeTransparent(self):
        # self.image_label.setGraphicsEffect(QGraphicsOpacityEffect(opacity=opacity))
        if self.isTransparent == False:
            self.isTransparent = True
            self.pixmap = QPixmap(self.file_name)
            self.pixmap.fill(Qt.transparent)
            self.image_label.setPixmap(self.pixmap)
        else:
            self.isTransparent = False
            self.pixmap = QPixmap(self.file_name)
            self.image_label.setPixmap(self.pixmap)

    def load_image(self):

        self.image_label.points = []
        options = QFileDialog.Options()
        self.file_name, _ = QFileDialog.getOpenFileName(self, "Выберите изображение", "", "Изображения (*.png *.jpg *.jpeg *.bmp *.gif)", options=options)

        if self.file_name != None:

            self.pixmap = QPixmap(self.file_name)
            self.image_label.setPixmap(self.pixmap)



        self.image_label.adjustSize()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())











