import sys
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QAction, QLineEdit, 
    QTabWidget, QCheckBox, QLabel
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings


class BrowserTab(QWebEngineView):
    """A single browser tab with URL bar sync and custom CSS injection."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings().setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        self.settings().setAttribute(QWebEngineSettings.WebRTCPublicInterfacesOnly, True)
        self.settings().setAttribute(QWebEngineSettings.LocalStorageEnabled, False)
        self.settings().setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, False)

        # Set custom User-Agent
        self.page().profile().setHttpUserAgent(
            "Mozilla/5.0 (Windows NT 10.0; rv:120.0) Gecko/20100101 Firefox/120.0"
        )

        # Connect signals
        self.urlChanged.connect(self.update_url_bar)
        self.loadFinished.connect(self.update_url_bar)

    def update_url_bar(self, url=None):
        """Update the main window's URL bar."""
        main_window = self.parent()  # Get reference to MainWindow
        if main_window and isinstance(main_window, MainWindow):
            main_window.url_bar.setText(self.url().toString())  # Update URL bar with active tab's URL


class MainWindow(QMainWindow):
    """Main application window with tabbed browsing."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("I2P Browser")
        self.setWindowIcon(QIcon("i2p_icon.png"))
        self.setGeometry(100, 100, 1200, 800)

        # Central widget: Tab widget for multiple tabs
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_url_bar_on_tab_switch)
        self.setCentralWidget(self.tabs)

        # Navigation toolbar
        self.navbar = QToolBar("Navigation")
        self.addToolBar(self.navbar)
        self.init_navbar()

        # Open initial tab
        self.add_new_tab(QUrl("https://google.com/"), "Home")

    def init_navbar(self):
        """Initialize navigation toolbar with buttons and actions."""
        # Navigation buttons
        back_btn = QAction('←', self)
        back_btn.triggered.connect(lambda: self.current_tab().back())
        self.navbar.addAction(back_btn)

        forward_btn = QAction('→', self)
        forward_btn.triggered.connect(lambda: self.current_tab().forward())
        self.navbar.addAction(forward_btn)

        reload_btn = QAction('↻', self)
        reload_btn.triggered.connect(lambda: self.current_tab().reload())
        self.navbar.addAction(reload_btn)

        home_btn = QAction('⌂', self)
        home_btn.triggered.connect(lambda: self.current_tab().setUrl(QUrl("https://google.com/")))
        self.navbar.addAction(home_btn)

        new_tab_btn = QAction('+', self)
        new_tab_btn.triggered.connect(lambda: self.add_new_tab(QUrl("https://google.com/"), "New Tab"))
        self.navbar.addAction(new_tab_btn)

        # URL bar
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.navbar.addWidget(self.url_bar)

        # Proxy toggle with iOS style
        self.proxy_switch = QCheckBox('Use I2P Proxy')
        self.proxy_switch.setChecked(True)
        self.proxy_switch.setStyleSheet("""
            QCheckBox {
                color: #ffffff;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 24px;
                height: 14px;
                border-radius: 7px;
                background-color: #2c2c2e;
            }
            QCheckBox::indicator:checked {
                background-color: #30d158;
            }
            QCheckBox::indicator:unchecked {
                background-color: #636366;
            }
        """)
        self.proxy_switch.stateChanged.connect(self.toggle_proxy)
        self.navbar.addWidget(self.proxy_switch)

        # Status label with modern styling
        self.status_label = QLabel("Proxy: Connected")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #30d158;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif;
                padding: 5px 10px;
                border-radius: 8px;
                background-color: #2c2c2e;
                margin-left: 10px;
            }
        """)
        self.navbar.addWidget(self.status_label)

    def current_tab(self):
        """Return the currently active tab."""
        return self.tabs.currentWidget()

    def add_new_tab(self, url=QUrl("about:blank"), label="New Tab"):
        """Add a new browser tab."""
        browser_tab = BrowserTab(self)
        browser_tab.setUrl(url)
        self.tabs.addTab(browser_tab, label)
        self.tabs.setCurrentWidget(browser_tab)

    def close_tab(self, index):
        """Close a tab by index."""
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)

    def navigate_to_url(self):
        """Navigate the current tab to the URL in the address bar."""
        url = self.url_bar.text()
        if not url.startswith(("http://", "https://")):
            url = "http://" + url
        self.current_tab().setUrl(QUrl(url))

    def update_url_bar_on_tab_switch(self):
        """Update the URL bar when switching tabs."""
        current_tab = self.current_tab()
        if current_tab:
            self.url_bar.setText(current_tab.url().toString())  # Update URL bar with active tab's URL
        else:
            self.url_bar.clear()

    def toggle_proxy(self, state):
        """Enable or disable proxy settings."""
        if state == Qt.Checked:
            self.status_label.setText("Proxy: Connected")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #30d158;
                    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif;
                    padding: 5px 10px;
                    border-radius: 8px;
                    background-color: #2c2c2e;
                    margin-left: 10px;
                }
            """)
        else:
            self.status_label.setText("Proxy: Disconnected")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #ff453a;
                    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif;
                    padding: 5px 10px;
                    border-radius: 8px;
                    background-color: #2c2c2e;
                    margin-left: 10px;
                }
            """)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("I2P Browser")
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
