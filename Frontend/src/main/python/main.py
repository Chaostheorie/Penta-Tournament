from fbs_runtime.application_context.PyQt5 import ApplicationContext
from simplejson.errors import JSONDecodeError
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import requests
import sys
import sched
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


class APIBIND:
    def __init__(self, username, password):
        self.session = requests.session()
        self.connect(username, password)
        self.username = username

    def connect(self, username, password):
        auth = requests.auth.HTTPBasicAuth(username=username, password=password)
        r = self.session.post("http://localhost:5000/api/user/token", auth=auth)
        if r.status_code != 200:
            raise CredentialsExption("Password or Username is Wrong")
        try:
            self.token = r.json()["token"]
        except JSONDecodeError:
            raise APIException("Server Response Invalid")

    def renew_token(self):
        r = self.repost("http://localhost:5000/api/user/token")
        self.token = r.json()["token"]

    def request(endpoint, payload, method="POST"):
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
            if r.status_code == 404:
                raise APIException(f"endpoint '{endpoint}' not found")
            elif r.status_code == 403:
                raise AuthorizationException(f"You're Not allowed to \
                                                access {endpoint}")
            elif r.status_code == 500:
                raise APIException("Server Side Error - Report was send")
            else:
                self.connect()

        return


class PentaTournament(ApplicationContext):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app.setStyleSheet(open(self.get_resource('style.qss')).read())
        # setWindowTitle("Penta Tournament Client")
        self.load_palette()
        self.connect()
        self.s = sched.scheduler(time.time, time.sleep)
        self.s.enter(500, 1, self.renew_token, (self))

    def renew_token(self):
        self.api.renew_token()
        self.s.enter(500, 1, self.renew_token, (self))

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
        StyleSheet = "QPushButton {color: white}"
        self.log_in_button.setStyleSheet(StyleSheet)
        self.log_in_button.setShortcut("Return")
        self.log_in_button.clicked.connect(self._connect)
        qr = self.log_in.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.log_in.move(qr.topLeft())

        self.log_in_layout.addWidget(self.log_in_button, 3, 2)
        self.log_in_layout.addWidget(self.username, 1, 2)
        self.log_in_layout.addWidget(self.password, 2, 2)
        self.username.setDisabled(False)
        self.password.setDisabled(False)
        self.log_in.setLayout(self.log_in_layout)
        self.log_in.show()
        self.username.setFocusPolicy(Qt.StrongFocus)
        self.username.setFocus()
        return

    def _connect(self):
        try:
            self.api = APIBIND(username=self.username.text(),
                               password=self.password.text())
            self.log_in.close()
            self.s.run()
            alert = QMessageBox()
            alert.setText("You are authenticated")
            alert.exec_()
        except CredentialsExption:
            alert = QMessageBox()
            alert.setText("Username or Password is wrong")
            alert.exec_()
            self.password.setText("")
        except APIException:
            alert = QMessageBox()
            alert.setText("Server Seems to be sending faulty responses \n \
                           Please Check your Network Connection")
            alert.exec_()

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
