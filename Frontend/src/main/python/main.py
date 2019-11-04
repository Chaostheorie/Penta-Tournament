from fbs_runtime.application_context.PyQt5 import ApplicationContext
from simplejson.errors import JSONDecodeError
from PyQt5 import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import requests
import sys
import time
import json


class CredentialsExption(Exception):
    """For Authentication failure by Server connection"""
    pass


class AuthorizationException(Exception):
    """Exception raised by unauthorized access 'Some permissions missing?"""


class APIException(Exception):
    """Exception for server side Errors 'They fucked up'"""
    pass


class APIException(Exception):
    """Exceptions for APIBIND Errors 'You fucked up'"""


class PicButton(QAbstractButton):
    def __init__(self, pixmap, parent=None):
        super(PicButton, self).__init__(parent)
        self.pixmap = pixmap

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(event.rect(), self.pixmap)

    def sizeHint(self):
        return self.pixmap.size()


class APIBIND:
    def __init__(self, username=None, password=None):
        self.session = requests.session()
        if username is not None and password is not None:
            self.connect(username, password)
            self.username = username

    def connect(self, username, password):
        auth = requests.auth.HTTPBasicAuth(username=username,
                                           password=password)
        r = self.session.get("http://localhost:5000/api/user/token", auth=auth)
        if r.status_code != 200:
            raise CredentialsExption("Password or Username is Wrong")
        try:
            r = r.json()
            self.token = r["token"]
            self.refresh_token = r["refresh_token"]
        except JSONDecodeError:
            raise APIException("Server Response Invalid")

    def renew_token(self):
        paylod = {"refresh_token": self.refresh_token, "password": None}
        r = self.get("http://localhost:5000/api/user/token", payload,
                     credentials=False, refresh=False)
        if r.status_code == 400:
            pass
        self.token = r.json()["token"]
        self.refresh_token = r["refresh_token"]

    def sign_up(self, username, password):
        payload = {"username": username, "password": password}
        return self.request("/api/user/sign-up", payload)

    def request(endpoint, payload, method="POST",
                credentials=True, refresh=True):
        if credentials:
            payload["username"] = self.token
            payload["password"] = None
        payload = json.dumps(payload)
        if method == "POST":
            r = self.session.post(f"http://localhost:5000/api/{endpoint}",
                                  payload)
        elif method == "PUT":
            r = self.session.put(f"http://localhost:5000/api/{endpoint}",
                                 payload)
        elif method == "GET":
            r = self.session.get(f"http://localhost:5000/api/{endpoint}",
                                 payload)
        elif method == "DELETE":
            r = self.session.delete(f"http://localhost:5000/api/{endpoint}",
                                    payload)
        else:
            raise APIException(f"Method '{method}' not allowed")
        if r.status_code != 200:
            if r.status_code == 401:
                self.renew_token()
            elif r.status_code == 404:
                raise APIException(f"endpoint '{endpoint}' not found")
            elif r.status_code == 403:
                raise AuthorizationException(f"You're Not allowed to \
                                                access {endpoint}")
            elif r.status_code == 500:
                raise APIException("Server Side Error - Report was send")
            elif r.status_code == 401:
                raise CredentialsExption("User not logged in")
            else:
                return r
        return r


class PentaTournament(ApplicationContext):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app.setStyleSheet(open(self.get_resource('style.qss')).read())
        # setWindowTitle("Penta Tournament Client")
        self.load_palette()
        self.api = APIBIND()
        self.connect()

    def connect(self):
        self.log_in = QWidget()
        self.log_in.resize(600, 25)
        self.log_in.setWindowTitle("Log In")
        self.log_in_layout = QGridLayout()
        self.username = QLineEdit(parent=self.log_in)
        self.username.setPlaceholderText("Username")
        self.password = QLineEdit(parent=self.log_in)
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)
        self.log_in_button = QPushButton("Log In", parent=self.log_in)
        self.sign_up_connect_button = QPushButton("Sign up",
                                                  parent=self.log_in)
        StyleSheet = "QPushButton {color: white}"
        self.log_in_button.setStyleSheet(StyleSheet)
        self.sign_up_connect_button.setStyleSheet(StyleSheet)
        self.log_in_button.setShortcut("Return")
        self.log_in_button.clicked.connect(self._connect)
        self.sign_up_connect_button.clicked.connect(self.Sign_up)
        qr = self.log_in.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.log_in.move(qr.topLeft())

        self.log_in_layout.addWidget(self.log_in_button, 3, 0)
        self.log_in_layout.addWidget(self.sign_up_connect_button, 3, 1)
        self.log_in_layout.addWidget(self.username, 1, 0, 1, 2)
        self.log_in_layout.addWidget(self.password, 2, 0, 1, 2)
        self.username.setDisabled(False)
        self.password.setDisabled(False)
        self.log_in.setLayout(self.log_in_layout)
        self.log_in.show()
        self.username.setFocusPolicy(Qt.StrongFocus)
        self.username.setFocus()
        return

    def _connect(self):
        try:
            self.api.connect(username=self.username.text(),
                             password=self.password.text())
            self._username = self.username.text()
            self.log_in.close()
            self.create_fronted()
        except CredentialsExption:
            self.alert("Username or Password is wrong")
            self.password.setText("")
        except APIException:
            self.alert("Server Seems to be sending faulty responses \n \
                        Please Check your Network Connection")

    def create_fronted(self):
        self.main_widget = QWidget()
        self.main_window = QMainWindow(parent=self.main_widget)
        # add all widgets
        self.home_btn = QPushButton()
        self.home_btn.minimumSize()
        home_icon = QIcon(self.get_resource("inapp.svg"))
        self.home_btn.setIcon(home_icon)
        self.home_btn.setMinimumSize(QSize(64, 64))
        StyleSheet = """QPushButton {border: solid;
                                    background-color: lightgreen; padding: 0px;
                                     }"""
        self.home_btn.setStyleSheet(StyleSheet)
        self.tournament_btn = QPushButton()
        self.tournament_btn.setIcon(QIcon(self.get_resource("tournaments.svg")
                                          ))
        StyleSheet = """QPushButton {border: solid;
                                     background-color: lightgray; padding: 0px;
                                     }"""
        self.tournament_btn.setStyleSheet(StyleSheet)
        self.tournament_btn.setMinimumSize(QSize(64, 64))
        self.leaderboard_btn = QPushButton()
        self.leaderboard_btn.setIcon(QIcon(self.get_resource("inapp.svg")))
        self.leaderboard_btn.setStyleSheet(StyleSheet)
        self.leaderboard_btn.setMinimumSize(QSize(64, 64))
        self.announcmentes_btn = QPushButton()
        self.announcmentes_btn.setIcon(QIcon(self.get_resource("announcments.svg")))
        self.announcmentes_btn.setStyleSheet(StyleSheet)
        self.announcmentes_btn.setMinimumSize(QSize(64, 64))
        self.home_btn.setMaximumSize(self.home_btn.iconSize())
        self.leaderboard_btn.setMaximumSize(self.leaderboard_btn.iconSize())
        self.announcmentes_btn.setMaximumSize(self.announcmentes_btn.iconSize())
        self.tournament_btn.setMaximumSize(self.tournament_btn.iconSize())

        self.home_btn.clicked.connect(self.button1)
        self.tournament_btn.clicked.connect(self.button2)
        self.leaderboard_btn.clicked.connect(self.button3)
        self.announcmentes_btn.clicked.connect(self.button4)

        # add tabs
        self.tab1 = self.home()
        self.tab2 = self.tournaments()
        self.tab3 = self.leaderboards()
        self.tab4 = self.announcmentes()
        left_layout = QVBoxLayout()
        left_layout.setAlignment(Qt.AlignTop)
        left_layout.addWidget(self.home_btn)
        left_layout.addWidget(self.tournament_btn)
        left_layout.addWidget(self.leaderboard_btn)
        left_layout.addWidget(self.announcmentes_btn, -1)
        left_layout.addStretch(5)
        left_layout.setSpacing(0)
        left_layout.setContentsMargins(QMargins(0, 0, 0, 0))
        left_widget = QWidget()
        left_widget.setLayout(left_layout)

        self.right_widget = QTabWidget()
        self.right_widget.tabBar().setObjectName("mainTab")

        self.right_widget.addTab(self.tab1, '')
        self.right_widget.addTab(self.tab2, '')
        self.right_widget.addTab(self.tab3, '')
        self.right_widget.addTab(self.tab4, '')

        self.right_widget.setCurrentIndex(0)
        self.right_widget.setStyleSheet('''QTabBar::tab{width: 0; \
            height: 0; margin: 0; padding: 0; border: none;}''')

        main_layout = QHBoxLayout()
        left_widget.setFixedWidth(self.home_btn.size().width())
        main_layout.addWidget(left_widget)
        main_layout.addWidget(self.right_widget)
        main_layout.setStretch(0, 40)
        main_layout.setStretch(1, 200)
        main_layout.setSpacing(0)
        self.frontend = QWidget()
        self.frontend.setLayout(main_layout)
        self.main_window.setCentralWidget(self.frontend)
        self.main_window.showMaximized()

    def button1(self):
        self.right_widget.setCurrentIndex(0)

    def button2(self):
        self.right_widget.setCurrentIndex(1)

    def button3(self):
        self.right_widget.setCurrentIndex(2)

    def button4(self):
        self.right_widget.setCurrentIndex(3)

    def home(self):
        main_layout = QGridLayout()
        #[main_layout.addWidget(QLabel())
        # for user in self.api.get_leaderboard()]
        main_layout.addWidget(QLabel("Leaderboard"), 0, 1)
        main = QWidget()
        main.setLayout(main_layout)
        return main

    def tournaments(self):
        main_layout = QVBoxLayout()
        main_layout.addWidget(QLabel('page 2'))
        main_layout.addStretch(5)
        main = QWidget()
        main.setLayout(main_layout)
        return main

    def leaderboards(self):
        main_layout = QVBoxLayout()
        main_layout.addWidget(QLabel('page 3'))
        main_layout.addStretch(5)
        main = QWidget()
        main.setLayout(main_layout)
        return main

    def announcmentes(self):
        main_layout = QVBoxLayout()
        main_layout.addWidget(QLabel('page 4'))
        main_layout.addStretch(5)
        main = QWidget()
        main.setLayout(main_layout)
        return main

    def _sign_up(self):
        if self.username.text().strip() == "":
            self.alert("Username needs to be at least one char")
        if self.password.text() == self.password_retype.text():
            t = self.api.sign_up(self.username.text().strip(),
                                 self.password.text())
            if t.status_code == 400:
                self.alert("Username is already used")
            else:
                self.alert(f"{self.username.text()} Created sucessfully")

        else:
            self.alert("Passwords didn't match")

    def alert(self, text):
        alert = QMessageBox()
        alert.setText(text)
        alert.exec_()

    def Sign_up(self):
        if self.log_in.isVisible():
            self.log_in.close()
        self.sign_up = QWidget()
        self.sign_up.resize(600, 25)
        self.sign_up.setWindowTitle("Log In")
        self.sign_up_layout = QGridLayout()
        self.username = QLineEdit(parent=self.sign_up)
        self.username.setPlaceholderText("Username")
        self.password = QLineEdit(parent=self.sign_up)
        self.password.setPlaceholderText("Password")
        self.password_retype = QLineEdit(parent=self.sign_up)
        self.password_retype.setPlaceholderText("Retype Password")
        self.password.setEchoMode(QLineEdit.Password)
        self.password_retype.setEchoMode(QLineEdit.Password)
        self.sign_up_button = QPushButton("Sign up", parent=self.sign_up)
        self.log_in_connect_button = QPushButton("Log in", parent=self.sign_up)
        StyleSheet = "QPushButton {color: white}"
        self.sign_up_button.setStyleSheet(StyleSheet)
        self.log_in_connect_button.setStyleSheet(StyleSheet)
        self.sign_up_button.setShortcut("Return")
        self.log_in_connect_button.clicked.connect(self._log_in)
        self.sign_up_button.clicked.connect(self._sign_up)
        qr = self.sign_up.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.sign_up.move(qr.topLeft())

        self.sign_up_layout.addWidget(self.sign_up_button, 4, 0)
        self.sign_up_layout.addWidget(self.log_in_connect_button, 4, 1)
        self.sign_up_layout.addWidget(self.username, 1, 0, 1, 2)
        self.sign_up_layout.addWidget(self.password_retype, 3, 0, 1, 2)
        self.sign_up_layout.addWidget(self.password, 2, 0, 1, 2)
        self.username.setDisabled(False)
        self.password.setDisabled(False)
        self.password_retype.setDisabled(False)
        self.sign_up.setLayout(self.sign_up_layout)
        self.sign_up.show()
        self.username.setFocusPolicy(Qt.StrongFocus)
        self.username.setFocus()
        return

    def _log_in(self):
        self.sign_up.close()
        return self.connect()

    def load_palette(self):
        """Set dark style theme"""
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Text, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))

        self.app.setStyle('Fusion')
        self.app.setPalette(dark_palette)
        return


if __name__ == '__main__':
    appctxt = PentaTournament()
    exit_code = appctxt.app.exec_()      # 2. Invoke appctxt.app.exec_()
    sys.exit(exit_code)
