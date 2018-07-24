import argparse
import sys
import os
import json

from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QRubberBand, QDialog, QLineEdit, QPushButton, QInputDialog, QDesktopWidget
from PyQt5.QtGui import QIcon, QPixmap, QCursor
from PIL import ImageGrab, ImageQt
from PyQt5 import sip


class App(QWidget):
    def __init__(self, save_path):
        super().__init__()

        self.save_path = save_path
        # Destkop Screenshot
        desktop_capture = ImageGrab.grab()
        desktop_capture.save('desktop_capture_temp.png')
        self.screen_size = QDesktopWidget().screenGeometry()
        QApplication.setOverrideCursor(
            QCursor(QtCore.Qt.CrossCursor)
        )

        self.area_defined = False
        self.imageName = None
        self.selected_area_center = None
        # Start the Qt UI
        self.initUI()
 
    def initUI(self):
        # Create widget
        self.image_label = QLabel(self)
        pixmap = QPixmap('desktop_capture_temp.png')
        self.image_label.setPixmap(pixmap)
        self.overlay_label = QLabel(self)
        self.overlay_label.setStyleSheet('background-color: rgba(0, 0, 0, 40);')
        self.overlay_label.setGeometry(self.screen_size)
        self.offset_label = QLabel(self)
        self.offset_label.setText('<font color="green" size=5>x</font>')
        self.help_text = QLabel(self)
        self.help_text.setGeometry(QtCore.QRect(((self.screen_size.width() - 350) / 2), 0, 350, 100))
        self.help_text.setText('<font color="red" size=14>Screen Snipping In Progress...</font>')
        # self.help_text.setStyleSheet('background-color: rgba(255, 255, 255, 100);')
        self.showFullScreen()

    def keyPressEvent(self, keyPressed):
        key = keyPressed.key()
        if key == QtCore.Qt.Key_Return or key == QtCore.Qt.Key_Enter:
            self.hide()
            self.getImageName()
            if self.save_path == 'None':
                self.cropQPixmap.save(os.path.normpath(self.imageName + '.png'))
            else:
                self.cropQPixmap.save(os.path.normpath(self.save_path + '/' + self.imageName + '.png'))
            try:
                self.offset_pos
            except AttributeError:
                if self.save_path == 'None':
                    with open(os.path.normpath(self.imageName + '.json'), 'w') as outfile:
                        image_data = {'clickOffset': [0, 0]}
                        json.dump(image_data, outfile, indent=4)
                else:
                    with open(os.path.normpath(self.save_path + '/' + self.imageName + '.json'), 'w') as outfile:
                        image_data = {'clickOffset': [0, 0]}
                        json.dump(image_data, outfile, indent=4)
            else:
                if self.save_path == 'None':
                    with open(os.path.normpath(self.imageName + '.json'), 'w') as outfile:
                        image_data = {'clickOffset': [self.offset_pos[0], self.offset_pos[1]]}
                        json.dump(image_data, outfile, indent=4)
                else:
                    with open(os.path.normpath(self.save_path + '/' + self.imageName + '.json'), 'w') as outfile:
                        image_data = {'clickOffset': [self.offset_pos[0], self.offset_pos[1]]}
                        json.dump(image_data, outfile, indent=4)
            self.close()
        elif key == QtCore.Qt.Key_Escape:
            self.close()

    def mousePressEvent(self, eventQMouseEvent):
        if self.area_defined == False:
            self.originQPoint = eventQMouseEvent.pos()
            self.currentQRubberBand = QRubberBand(QRubberBand.Rectangle, self)
            self.currentQRubberBand.setGeometry(QtCore.QRect(self.originQPoint, QtCore.QSize()))
            self.currentQRubberBand.show()
        elif self.area_defined == True:
            self.offset_label.move((eventQMouseEvent.pos().x() - self.offset_label.geometry().width()), (eventQMouseEvent.pos().y() - self.offset_label.geometry().height()))
            click_location = [eventQMouseEvent.pos().x(), eventQMouseEvent.pos().y()]
            self.offset_pos = [(click_location[0] - self.selected_area_center[0]), (click_location[1] - self.selected_area_center[1])]

    def mouseMoveEvent(self, eventQMouseEvent):
        if self.area_defined == False:
            self.currentQRubberBand.setGeometry(QtCore.QRect(self.originQPoint, eventQMouseEvent.pos()).normalized())

    def mouseReleaseEvent(self, eventQMouseEvent):
        if self.area_defined == False:
            currentQRect = self.currentQRubberBand.geometry()
            self.selected_area_center = [currentQRect.center().x(), currentQRect.center().y()]
            self.cropQPixmap = self.image_label.pixmap().copy(currentQRect)
            self.area_defined = True

    def getImageName(self):
        text, okPressed = QInputDialog.getText(self, "Get Image Name","Type Image Name:", QLineEdit.Normal, "")
        if okPressed and text != '':
            self.imageName = text

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Tingus Start Options.')
    parser.add_argument('--save', help='Save location of image', type=str)
    args = parser.parse_args()

    app = QApplication(sys.argv)
    if args.save:
        ex = App(args.save)
    else:
        ex = App('None')

    sys.exit(app.exec_())
