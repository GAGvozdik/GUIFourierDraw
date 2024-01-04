import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QLabel, QWidget, QFileDialog
from PyQt5.QtGui import QPixmap, QIcon, QPainter, QPen



from PyQt5.QtCore import Qt, QPoint

class ImageDisplayApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Image Display App')
        self.setGeometry(100, 100, 640, 480)  # Задание начального размера окна приложения

        self.image_label = QLabel(self)  # Метка для отображения изображения
        self.image_label.setAlignment(Qt.AlignCenter)  # Выравнивание изображения по центру

        self.load_button = QPushButton('Load Image', self)
        self.load_button.setIcon(QIcon('plus_icon.png'))  # Иконка кнопки
        self.load_button.clicked.connect(self.load_image)  # Обработчик нажатия кнопки

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.load_button)
        main_layout.addWidget(self.image_label)

        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.image_label.mousePressEvent = self.get_mouse_coordinates
        self.image = None
        self.original_pixmap = None
        self.points = []

    def load_image(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)", options=options)
        if filename:
            self.original_pixmap = QPixmap(filename)
            self.show_image()
            # self.setGeometry(0, 0, self.original_pixmap.width(), self.original_pixmap.height())

    def show_image(self):
        self.image = self.original_pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio,
                                                 Qt.SmoothTransformation)  # Масштабирование изображения
        self.image_label.setPixmap(self.image)  # Отображение изображения
        self.points = []  # Очистка списка точек
        # self.setFixedSize(self.image.width(), self.image.height())  # Установка фиксированного размера окна

    def get_mouse_coordinates(self, event):
        if self.original_pixmap:
            # x = event.pos().x() - (self.image_label.width() - self.image.width()) / 2
            # y = event.pos().y() - (self.image_label.height() - self.image.height()) / 2
            x = event.pos().x() + (self.image_label.width() - self.width()) / 2
            x = self.image_label.width() * x / self.width()
            y = event.pos().y() + (self.image.height() - 480) / 2
            y = self.image_label.height() * y / self.height()


            self.points.append((x, y))  # Добавление скорректированных координат в список
            print(f"Добавлена точка: ({x}, {y})")  # Вывод скорректированных координат в консоль
            self.draw_points()  # Вызов метода для рисования точек

    def mouseMoveEvent(self, event):
        if self.original_pixmap:
            x = event.pos().x() + (self.image_label.width() - self.width()) / 2
            x = self.image_label.width() * x / self.width()
            y = event.pos().y() + (self.image.height() - 480) / 2
            y = self.image_label.height() * y / self.height()
            # x = event.pos().x() - (self.image_label.width() - self.image.width()) / 2
            # y = event.pos().y() - (self.image_label.height() - self.image.height()) / 2
            self.statusBar().showMessage(f'Координаты: {x}, {y}')

    def draw_points(self):
        temp_image = QPixmap(self.original_pixmap.size())
        temp_image.fill(Qt.transparent)
        painter = QPainter(temp_image)
        painter.drawPixmap(0, 0, self.original_pixmap)

        painter.setPen(QPen(Qt.black, 5, Qt.SolidLine))
        for point in self.points:
            x, y = point  # Распаковываем координаты x и y из точки
            painter.drawEllipse(x, y, 5, 5)  # Рисуем эллипс в центре (x, y)


        painter.drawEllipse(0, 0, 25, 25)  # Draw ellipse centered at (x, y)
        painter.drawEllipse(100, 100, 25, 25)  # Draw ellipse centered at (x, y)
        painter.end()
        self.image = temp_image.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(self.image)
if __name__ == '__main__':
    app = QApplication(sys.argv)
    image_display_app = ImageDisplayApp()
    image_display_app.show()
    sys.exit(app.exec_())
