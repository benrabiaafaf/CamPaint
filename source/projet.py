import os
import sys
from datetime import datetime

from PyQt5.QtCore import QTimer, Qt, QSize
from PyQt5.QtGui import QPixmap, QImage, QIcon, QFont
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QHBoxLayout, QDesktopWidget, QPushButton, QVBoxLayout, \
    QSlider, QColorDialog, QMessageBox, QFileDialog
from cv2 import VideoCapture, VideoWriter, VideoWriter_fourcc, \
    line, circle, flip, waitKey, imread, resize, imwrite, cvtColor, \
    CAP_PROP_FRAME_HEIGHT, CAP_PROP_FRAME_WIDTH, COLOR_BGR2RGB
from numpy import full, array, where, amax, amin, ones, sqrt, uint8


class Application(QWidget):

    def __init__(self):

        self.colors_detection = False
        self.record = False
        self.pencil_active = False
        self.eraser_active = False
        self.video_recorded = False
        self.board_is_upload = False
        self.distance = None
        self.path = ''
        self.seuil = 30
        self.d_min = 30
        self.pencil_color = (0, 0, 0)
        self.cursor_size = 1

        self.cap = VideoCapture(0)
        self.w = self.cap.get(CAP_PROP_FRAME_WIDTH)
        self.h = self.cap.get(CAP_PROP_FRAME_HEIGHT)

        self.center_1 = (int(self.w / 12 * 6), int(self.h / 12 * 9))
        self.center_2 = (int(self.w / 12 * 8), int(self.h / 12 * 8))

        self.setGUI()

        if self.cap.isOpened():

            self.show()
            self.center()
            self.path = QFileDialog.getExistingDirectory(self,
                                                         "Choisir un dossier pour enregistrer les captures et les vidéos")
            self.timer = QTimer()
            self.timer.setInterval(1)
            self.timer.timeout.connect(self.run)
            self.timer.start()
        else:
            msg_box = QMessageBox()
            msg_box.setWindowTitle("Erreur")
            msg_box.setText("Impossible d'ouvrirr la caméra")
            msg_box.setIconPixmap(QPixmap('icons\\no-camera.png').scaledToHeight(50, Qt.SmoothTransformation))
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec_()
            sys.exit()

    def run(self):

        if not self.colors_detection:
            self.get_frame()
            self.draw_circles()
            self.display_frame()

        else:
            self.get_frame()
            # self.detect_colors()
            self.detect_colors_classic()
            self.process()
            self.record_video()
            self.display_frame()

    def keyPressEvent(self, keyEvent):
        if keyEvent.key() in [Qt.Key_Enter, Qt.Key_Return]:
            color = self.frame[self.center_1[1], self.center_1[0]]
            self.color_1 = (int(color[0]), int(color[1]), int(color[2]))
            color = self.frame[self.center_2[1], self.center_2[0]]
            self.color_2 = (int(color[0]), int(color[1]), int(color[2]))
            self.tools_enabled(True)
            self.colors_detection = True
            self.info_label.hide()
            self.pencil_btn.click()

    def process(self):
        if self.pencil_active is True:
            self.draw(self.pencil_color)
        elif self.eraser_active is True:
            self.draw((255, 255, 255))

    def record_video(self):
        if self.record is True:
            self.video_writer.write(cvtColor(self.board, COLOR_BGR2RGB))

    def draw(self, color):

        if self.center_1 is not None and self.center_2 is not None:
            x_1 = self.center_1[0]
            y_1 = self.center_1[1]
            x_2 = self.center_2[0]
            y_2 = self.center_2[1]

            x = int((x_1 + x_2) / 2)
            y = int((y_1 + y_2) / 2)

            # line(self.frame, (x, y), (x, y), (255, 0, 0), 5)

            d = sqrt(pow(x_1 - x_2, 2) + pow(y_1 - y_2, 2)) - self.radius_1 - self.radius_2
            self.distance = d
            if d <= self.d_min:
                line(self.board, (x, y), (x, y), color, self.cursor_size)
            else:
                circle(self.board_copy, (x, y), int(self.cursor_size / 2), (0, 0, 0), 2)

            line(self.frame, (x, y), (x, y), color, 5)

    def draw_circles(self):

        circle(self.frame, self.center_1, 15, (255, 0, 0), 1)
        circle(self.frame, self.center_2, 15, (255, 0, 0), 1)

    def detect_colors(self):

        img = array(self.frame).astype(int)

        r = self.color_1[0]
        g = self.color_1[1]
        b = self.color_1[2]

        idx = where(sqrt(pow(img[:, :, 0] - r, 2) + pow(img[:, :, 1] - g, 2) + pow(img[:, :, 2] - b, 2)) <= self.seuil)

        if len(idx[0]) > 0 and len(idx[1]) > 0:
            x_min = amin(idx[1])
            x_max = amax(idx[1])
            y_min = amin(idx[0])
            y_max = amax(idx[0])

            x = int((x_max + x_min) / 2)
            y = int((y_max + y_min) / 2)
            self.center_1 = (x, y)
            self.radius_1 = int(sqrt(pow(x_max - x_min, 2) + pow(y_max - y_min, 2)) / 2)
            circle(self.frame, self.center_1, self.radius_1, self.color_1, 1)
            self.frame[idx] = (255, 0, 0)

        else:
            self.center_1 = None

        r = self.color_2[0]
        g = self.color_2[1]
        b = self.color_2[2]

        idx = where(sqrt(pow(img[:, :, 0] - r, 2) + pow(img[:, :, 1] - g, 2) + pow(img[:, :, 2] - b, 2)) <= self.seuil)
        if len(idx[0]) > 0 and len(idx[1]) > 0:
            x_min = amin(idx[1])
            x_max = amax(idx[1])
            y_min = amin(idx[0])
            y_max = amax(idx[0])
            x = int((x_max + x_min) / 2)
            y = int((y_max + y_min) / 2)
            self.center_2 = (x, y)
            self.radius_2 = int(sqrt(pow(x_max - x_min, 2) + pow(y_max - y_min, 2)) / 2)
            circle(self.frame, self.center_2, self.radius_2, self.color_2, 1)
            self.frame[idx] = (255, 0, 0)
        else:
            self.center_2 = None

    def detect_colors_classic(self):
        (r_1, g_1, b_1) = self.color_1
        (r_2, g_2, b_2) = self.color_2

        x_min_1 = int(self.w)
        x_max_1 = 0
        y_min_1 = int(self.h)
        y_max_1 = 0

        x_min_2 = int(self.w)
        x_max_2 = 0
        y_min_2 = int(self.h)
        y_max_2 = 0

        n_1 = 0
        n_2 = 0
        for x in range(int(self.w)):
            for y in range(int(self.h)):
                (r, g, b) = self.frame[y, x]
                d_1 = sqrt(pow(r_1 - r, 2) + pow(g_1 - g, 2) + pow(b_1 - b, 2))
                d_2 = sqrt(pow(r_2 - r, 2) + pow(g_2 - g, 2) + pow(b_2 - b, 2))
                if d_1 <= self.seuil:
                    self.frame[y, x] = (255, 0, 0)
                    x_min_1 = min(x, x_min_1)
                    x_max_1 = max(x, x_max_1)
                    y_min_1 = min(y, y_min_1)
                    y_max_1 = max(y, y_max_1)
                    n_1 += 1
                elif d_2 <= self.seuil:
                    self.frame[y, x] = (255, 0, 0)
                    x_min_2 = min(x, x_min_2)
                    x_max_2 = max(x, x_max_2)
                    y_min_2 = min(y, y_min_2)
                    y_max_2 = max(y, y_max_2)
                    n_2 += 1
        if n_1 >= 0:
            x = int((x_max_1 + x_min_1) / 2)
            y = int((y_max_1 + y_min_1) / 2)
            self.center_1 = (x, y)
            self.radius_1 = int(sqrt(pow(x_max_1 - x_min_1, 2) + pow(y_max_1 - y_min_1, 2)) / 2)
            circle(self.frame, self.center_1, self.radius_1, self.color_1, 1)
        else:
            self.center_1 = None
        if n_2 >= 0:
            x = int((x_max_2 + x_min_2) / 2)
            y = int((y_max_2 + y_min_2) / 2)
            self.center_2 = (x, y)
            self.radius_2 = int(sqrt(pow(x_max_2 - x_min_2, 2) + pow(y_max_2 - y_min_2, 2)) / 2)
            circle(self.frame, self.center_2, self.radius_2, self.color_2, 1)
        else:
            self.center_1 = None

    def get_frame(self):

        _, self.frame = self.cap.read()
        print(self.frame.shape)
        self.frame = cvtColor(self.frame, COLOR_BGR2RGB)
        self.frame = flip(self.frame, 1)
        if not self.colors_detection and not self.board_is_upload:
            self.board = full(self.frame.shape, (255, 255, 255), dtype=self.frame.dtype)
        self.board_copy = self.board.copy()

    def display_frame(self):
        self.video_frame.setPixmap(QPixmap.fromImage(QImage(self.frame, self.w, self.h, QImage.Format_RGB888)))
        if self.distance is None or self.distance > self.d_min:
            self.board_frame.setPixmap(QPixmap.fromImage(QImage(self.board_copy, self.w, self.h, QImage.Format_RGB888)))
        else:
            self.board_frame.setPixmap(QPixmap.fromImage(QImage(self.board, self.w, self.h, QImage.Format_RGB888)))
        waitKey(1)

    def setGUI(self):
        super(QWidget, self).__init__()

        self.video_frame = QLabel()
        self.video_frame.setFixedWidth(self.w)
        self.video_frame.setFixedHeight(self.h)
        self.board_frame = QLabel()
        self.board_frame.setFixedWidth(self.w)
        self.board_frame.setFixedHeight(self.h)

        self.info_label = QLabel(
            "Mettez deux couleurs distinctes à l'interieur des cercles rouges de votre camera puis cliquez sur 'Entrée' pour commencer le dessin")
        self.info_label.setFont(QFont('Droid Sans', 10, QFont.Bold))

        self.pencil_btn = self.create_btn('pencil.png')
        self.eraser_btn = self.create_btn('gomme.png')
        self.palette_btn = self.create_btn('palette.png')
        self.save_btn = self.create_btn('save.png')
        self.video_btn = self.create_btn('video.png')
        self.quit_btn = self.create_btn('logout.png')
        self.upload_btn = self.create_btn('upload.png')

        self.cursor_shape = QLabel()
        img = ones((60, 60, 3), uint8) * 220
        self.cursor_shape.setPixmap(QPixmap.fromImage(QImage(img, img.shape[0], img.shape[1], QImage.Format_RGB888)))

        self.slider = QSlider(Qt.Horizontal)
        self.slider.valueChanged.connect(self.slider_changes)
        self.slider.setMinimum(1)
        self.slider.setMaximum(41)
        self.slider.setSingleStep(2)
        self.slider.setTickPosition(QSlider.TicksLeft)
        self.slider.setTickInterval(2)

        self.palette_btn.clicked.connect(self.palette_btn_clicked)
        self.pencil_btn.clicked.connect(self.pencil_btn_clicked)
        self.eraser_btn.clicked.connect(self.eraser_ban_clicked)
        self.video_btn.clicked.connect(self.video_btn_clicked)
        self.save_btn.clicked.connect(self.save_btn_clicked)
        self.quit_btn.clicked.connect(self.closeEvent)
        self.upload_btn.clicked.connect(self.upload_btn_clicked)

        tools_layout = QHBoxLayout()
        frames_layout = QHBoxLayout()

        tools_layout.addWidget(self.quit_btn)
        tools_layout.addWidget(self.upload_btn)
        tools_layout.addWidget(self.save_btn)
        tools_layout.addWidget(self.video_btn)
        tools_layout.addWidget(self.eraser_btn)
        tools_layout.addWidget(self.palette_btn)
        tools_layout.addWidget(self.pencil_btn)
        tools_layout.addWidget(self.cursor_shape)
        tools_layout.addWidget(self.slider)

        frames_layout.addWidget(self.video_frame)
        frames_layout.addWidget(self.board_frame)

        v_layout = QVBoxLayout()
        v_layout.addLayout(tools_layout)
        v_layout.addLayout(frames_layout)
        v_layout.addWidget(self.info_label)

        self.setLayout(v_layout)

        self.tools_enabled(False)

        self.setWindowTitle('CamPaint')
        self.setWindowIcon(QIcon(self.resource_path('tools.ico')))

    def upload_btn_clicked(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choisir une image")
        if len(path) > 0:
            img = imread(path)
            img = cvtColor(img, COLOR_BGR2RGB)
            img = resize(img, (int(self.w), int(self.h)))
            self.board = img
            self.board_is_upload = True

    def save_btn_clicked(self):
        f = datetime.now()
        f = self.path + '/' + str(f.date()) + '-' + str(f.hour) + '-' + str(f.minute) + '.jpg'
        imwrite(f, cvtColor(self.board, COLOR_BGR2RGB))

    def video_btn_clicked(self):
        self.record = not self.record

        if self.record is True:
            self.video_btn.setStyleSheet("background-color: lightgrey;")
        else:
            self.video_btn.setStyleSheet("background-color: none;")

        if self.video_recorded is False:
            self.video_recorded = True
            time = datetime.now()
            f = self.path + '/' + str(time.date()) + '-' + str(time.hour) + '-' + str(time.minute) + '.avi'
            self.video_writer = VideoWriter(f, VideoWriter_fourcc(*'XVID'), 10, (int(self.w), int(self.h)))

    def tools_enabled(self, bool):
        self.pencil_btn.setEnabled(bool)
        self.eraser_btn.setEnabled(bool)
        self.palette_btn.setEnabled(bool)
        self.save_btn.setEnabled(bool)
        self.video_btn.setEnabled(bool)
        self.slider.setEnabled(bool)

    def center(self):
        frame = self.frameGeometry()
        center_point = QDesktopWidget().availableGeometry().center()
        frame.moveCenter(center_point)
        self.move(frame.topLeft())

    def closeEvent(self, event):
        if self.video_recorded is True:
            self.video_writer.release()
        self.cap.release()
        self.close()
        sys.exit()

    def create_btn(self, icon):
        btn = QPushButton()
        btn.setIcon(QIcon(QPixmap(self.resource_path(icon))))
        btn.setIconSize(QSize(50, 50))
        btn.setStyleSheet("borer: 0px solid black;")

        return btn

    def slider_changes(self):
        self.cursor_size = self.slider.value()
        if self.pencil_active is True:
            self.cursor_shape.setStyleSheet("background-color: white")
            img = ones((60, 60, 3), uint8) * 255
            line(img, (30, 30), (30, 30), self.pencil_color, self.cursor_size)
            self.cursor_shape.setPixmap(
                QPixmap.fromImage(QImage(img, img.shape[0], img.shape[1], QImage.Format_RGB888)))
        elif self.eraser_active is True:
            self.cursor_shape.setStyleSheet("background-color: white")
            img = ones((60, 60, 3), uint8) * 0
            line(img, (30, 30), (30, 30), (255, 255, 255), self.cursor_size)
            self.cursor_shape.setPixmap(
                QPixmap.fromImage(QImage(img, img.shape[0], img.shape[1], QImage.Format_RGB888)))

    def palette_btn_clicked(self):
        color = QColorDialog.getColor()
        color = (color.red(), color.green(), color.blue())
        self.pencil_color = color
        self.slider_changes()

    def pencil_btn_clicked(self):
        self.pencil_active = not self.pencil_active
        if self.pencil_active is True:
            self.pencil_btn.setStyleSheet("background-color: lightgrey;")
            if self.eraser_active is True:
                self.eraser_btn.click()
        else:
            self.pencil_btn.setStyleSheet("background-color: none;")
        self.slider_changes()

    def eraser_ban_clicked(self):
        self.eraser_active = not self.eraser_active
        if self.eraser_active is True:
            self.eraser_btn.setStyleSheet("background-color: lightgrey;")
            if self.pencil_active is True:
                self.pencil_btn.click()
        else:
            self.eraser_btn.setStyleSheet("background-color: none;")
        self.slider_changes()

    def resource_path(self, icon_name):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, 'icons\\' + icon_name)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Application()
    sys.exit(app.exec_())
