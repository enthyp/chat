import sys
from PyQt5 import QtCore, QtGui, QtWidgets


class UIMainWindow(object):
    def setupUi(self, mainWindow):
        mainWindow.setObjectName("mainWindow")
        mainWindow.resize(406, 686)
        self.centralwidget = QtWidgets.QWidget(mainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.textBrowser = QtWidgets.QTextBrowser(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(13)
        font.setBold(False)
        font.setWeight(50)
        self.textBrowser.setFont(font)
        self.textBrowser.setObjectName("textBrowser")
        self.verticalLayout.addWidget(self.textBrowser)
        self.plainTextEdit = QtWidgets.QPlainTextEdit(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.plainTextEdit.sizePolicy().hasHeightForWidth())
        self.plainTextEdit.setSizePolicy(sizePolicy)
        self.plainTextEdit.setMaximumSize(QtCore.QSize(16777215, 100))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.plainTextEdit.setFont(font)
        self.plainTextEdit.setObjectName("plainTextEdit")
        self.verticalLayout.addWidget(self.plainTextEdit)
        self.verticalLayout_2.addLayout(self.verticalLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.pushButton_2 = QtWidgets.QPushButton(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_2.sizePolicy().hasHeightForWidth())
        self.pushButton_2.setSizePolicy(sizePolicy)
        self.pushButton_2.setObjectName("pushButton_2")
        self.horizontalLayout_2.addWidget(self.pushButton_2)
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton.sizePolicy().hasHeightForWidth())
        self.pushButton.setSizePolicy(sizePolicy)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout_2.addWidget(self.pushButton)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        mainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(mainWindow)
        self.statusbar.setObjectName("statusbar")
        mainWindow.setStatusBar(self.statusbar)
        mainWindow.setStyleSheet("QMainWindow {background: '#303030';}")
        mainWindow.show()

        self.plainTextEdit.setStyleSheet("QPlainTextEdit {background-color: '#5e5e5e'; color: white}")
        self.plainTextEdit.show()

        self.textBrowser.setStyleSheet("QTextBrowser {background: '#5e5e5e'; color: white}")
        self.textBrowser.show()

        self.pushButton.setStyleSheet("background-color: green")
        self.pushButton_2.setStyleSheet("background-color: red")

        self.retranslateUi(mainWindow)
        QtCore.QMetaObject.connectSlotsByName(mainWindow)

    def retranslateUi(self, mainWindow):
        _translate = QtCore.QCoreApplication.translate
        mainWindow.setWindowTitle(_translate("mainWindow", "MainWindow"))
        self.pushButton_2.setText(_translate("mainWindow", "Quit Channel"))
        self.pushButton.setText(_translate("mainWindow", "Send"))


class GUI(QtWidgets.QMainWindow):
    def __init__(self, app, parent=None):
        super(GUI, self).__init__(parent)
        self.ui = UIMainWindow()
        self.ui.setupUi(self)
        self.ui.pushButton.clicked.connect(self.send_message)
        self.ui.pushButton_2.clicked.connect(self.quit_channel)

        self.ui.plainTextEdit.installEventFilter(self)
        self.client = None
        self.app = app
        self.show()

    def send_message(self):
        message = self.ui.plainTextEdit.toPlainText()
        self.ui.textBrowser.append(message)
        if message.strip(" ") != "" and self.client:
            self.client.handle_input(message.strip(" "))
        self.ui.plainTextEdit.clear()

    def quit_channel(self):
        if self.client:
            self.client.handle_input("/LEAVE")

    def eventFilter(self, obj, event):
        if self.ui.plainTextEdit is obj and event.type() == QtCore.QEvent.KeyPress:
            if event.key() in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
                self.send_message()
                return True
            elif event.key() == QtCore.Qt.Key_Escape:
                self.client.close_connection()
                return True
        return super(GUI, self).eventFilter(obj, event)

    def send(self, line, prefix='', color='WHITE'):
        self.ui.textBrowser.append(prefix + line)

    def register_client(self, client):
        self.client = client

    def lose_connection(self):
        self.close()
        self.app.quit()
        sys.exit(self.app.exec_())
