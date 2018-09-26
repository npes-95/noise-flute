import sys
from PyQt5.QtCore import \
    Qt, pyqtSlot
from PyQt5.QtWidgets import \
    QApplication, QWidget, \
    QSlider, QPushButton, \
    QMessageBox, \
    QVBoxLayout, QHBoxLayout


class ExecutiveToy(QWidget):

    def __init__(self, parent = None):
        super().__init__(parent)
        self.create_UI(parent)


    def create_UI(self, parent):
        # Create a slider and two buttons
        self.mySlider = QSlider(Qt.Horizontal)
        self.showButton = \
            QPushButton(self.tr('&Show Value'))
        self.quitButton = \
            QPushButton(self.tr('&Quit'))

        # No parent: we're going to add this
        # to vLayout.
        hLayout = QHBoxLayout()
        hLayout.addWidget(self.showButton)
        hLayout.addStretch(1)
        hLayout.addWidget(self.quitButton)

        # parent = self: this is the
        # "top level" layout
        vLayout = QVBoxLayout(self)
        vLayout.addWidget(self.mySlider)
        vLayout.addLayout(hLayout)

        self.quitButton.clicked.connect(
            self.quitClicked
        )
        self.showButton.clicked.connect(
            self.showClicked
        )

    # Now the slots which accept events
    @pyqtSlot()
    def quitClicked(self):
        self.close()

    @pyqtSlot()
    def showClicked(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)

        msg.setText('Current Slider Value')
        msg.setInformativeText(
            'When requested, value was '
            + str(self.mySlider.value())
        )
        msg.setWindowTitle('mySlider')
        msg.setDetailedText('That is all I know')
        msg.setStandardButtons(QMessageBox.Ok)

        msg.exec()



if __name__ == "__main__":
  app = QApplication(sys.argv)
  window = ExecutiveToy()
  window.show()
  sys.exit(app.exec_())
