"""Set dark style theme""" self.dark_palette = QPalette()

self.dark_palette.setColor(QPalette.Window, QColor(53, 53, 53)) self.dark_palette.setColor(QPalette.WindowText, QColor(255, 255, 255)) self.dark_palette.setColor(QPalette.Base, QColor(25, 25, 25)) self.dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53)) self.dark_palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255)) self.dark_palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255)) self.dark_palette.setColor(QPalette.Text, QColor(255, 255, 255)) self.dark_palette.setColor(QPalette.Button, QColor(53, 53, 53)) self.dark_palette.setColor(QPalette.ButtonText, QColor(255, 255, 255)) self.dark_palette.setColor(QPalette.BrightText, QColor(255, 0, 0)) self.dark_palette.setColor(QPalette.Link, QColor(42, 130, 218)) self.dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218)) self.dark_palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))

self.app.setPalette(self.dark_palette)

self.app.setStyleSheet("""QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }""")
