import sys
import os
import json
from PySide6.QtCore import QUrl, QSize, Qt
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QToolBar,
    QLineEdit,
    QProgressBar,
    QStatusBar,
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QMenu,
    QPushButton,
    QDialog,
    QListWidget,
    QHBoxLayout,
    QMessageBox,
    QTabWidget,
    QToolButton,
    QStyle
)
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import (
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineSettings,
    QWebEngineUrlRequestInterceptor,
    QWebEngineUrlRequestInfo,
)

# ----------------------------------------------------------------------------
#  Ad‑blocking interceptor
# ----------------------------------------------------------------------------
class AdBlocker(QWebEngineUrlRequestInterceptor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.blocklist = [
            "doubleclick.net",
            "googlesyndication.com",
            "adservice.google.",
            "ads.youtube.com",
            "ads.yahoo.",
            "taboola.com",
            "outbrain.com",
            "facebook.com/tr/",
            "pixel.",
        ]

    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        if any(p in info.requestUrl().toString() for p in self.blocklist):
            info.block(True)
        else:
            info.block(False)


class ListDialog(QDialog):
    def __init__(self, title: str, items: list[str]):
        super().__init__()
        self.setWindowTitle(title)
        self.resize(500, 400)
        layout = QVBoxLayout(self)
        self.listw = QListWidget()
        self.listw.addItems(items)
        layout.addWidget(self.listw)
        self.listw.itemDoubleClicked.connect(self.accept)

    def selected_text(self) -> str | None:
        itm = self.listw.currentItem()
        return itm.text() if itm else None


class Browser(QMainWindow):
    def _tune_settings(self):
        settings = self.view.settings()
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)

    def __init__(self, *, incognito: bool = False):
        super().__init__()
        self.incognito = incognito

        self.setWindowTitle(f"PySide Browser{' (Incognito)' if self.incognito else ''}")
        self.resize(1200, 800)

        self.tabs = QTabWidget(self)
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.setDocumentMode(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.tab_changed)
        self.setCentralWidget(self.tabs)

        nav = QToolBar("Navigation", self)
        nav.setIconSize(QSize(24, 24))
        self.addToolBar(nav)

        self.back_act = QAction("←", self, triggered=lambda: self.view.back())
        self.fwd_act = QAction("→", self, triggered=lambda: self.view.forward())
        self.reload_act = QAction("↻", self, triggered=lambda: self.view.reload())
        self.home_act = QAction("⌂", self, triggered=self.browser_home)
        self.ua_act = QAction("🔍", self, triggered=self.show_user_agent)
        self.incog_act = QAction("🕵️", self, triggered=self.open_incognito)
        nav.addActions([
            self.back_act,
            self.fwd_act,
            self.reload_act,
            self.home_act,
            self.ua_act,
            self.incog_act,
        ])

        self.url_bar = QLineEdit(self, returnPressed=self.go_to_url)
        nav.addWidget(self.url_bar)

        self.menu_btn = QPushButton("⋮")
        self.menu_btn.setFixedSize(30, 30)
        self.menu_menu = QMenu(self.menu_btn)
        self.menu_menu.addAction("📥 Downloads", self.show_downloads)
        self.menu_menu.addAction("🕓 History", self.show_history)
        self.menu_menu.addAction("🔖 Bookmarks", self.show_bookmarks)
        self.menu_menu.addSeparator()
        self.menu_menu.addAction("⭐ Add Bookmark", self.add_bookmark)
        self.menu_btn.setMenu(self.menu_menu)
        nav.addWidget(self.menu_btn)

        self.new_tab_btn = QToolButton()
        self.new_tab_btn.setText("+")
        self.new_tab_btn.setFixedSize(30, 30)
        self.new_tab_btn.clicked.connect(lambda _: self.new_tab())
        nav.addWidget(self.new_tab_btn)

        self.downloads: list[str] = []
        self.history: list[str] = []
        self.bookmarks_path = os.path.join(os.path.expanduser("~"), ".pyside_browser_profile", "bookmarks.json")
        os.makedirs(os.path.dirname(self.bookmarks_path), exist_ok=True)
        try:
            self.bookmarks = json.load(open(self.bookmarks_path))
        except Exception:
            self.bookmarks = []

        self.new_tab()

        self.status = QStatusBar(self)
        self.setStatusBar(self.status)
        self.progress = QProgressBar(maximumWidth=120, visible=False)
        self.status.addPermanentWidget(self.progress)

    def _create_profile(self) -> QWebEngineProfile:
        if self.incognito:
            p = QWebEngineProfile(self)
            p.setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)
        else:
            root = os.path.join(os.path.expanduser("~"), ".pyside_browser_profile")
            os.makedirs(root, exist_ok=True)
            p = QWebEngineProfile("user-profile", self)
            p.setCachePath(os.path.join(root, "cache"))
            p.setPersistentStoragePath(os.path.join(root, "storage"))
            p.setPersistentCookiesPolicy(QWebEngineProfile.ForcePersistentCookies)
        p.setHttpUserAgent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) "
            "Gecko/20100101 Firefox/122.0"
        )
        return p

    def _toggle_progress(self, start: bool):
        self.progress.setVisible(start)
        self.progress.setValue(0)
        if start:
            self.status.showMessage("Loading…")

    def progress_value(self, v: int):
        self.progress.setValue(v)

    def _load_finished(self, ok: bool):
        self._toggle_progress(False)
        self.status.showMessage("Loaded" if ok else "Load failed", 3000)
        self._update_nav_state()

    def _update_nav_state(self):
        hist = self.view.history()
        self.back_act.setEnabled(hist.canGoBack())
        self.fwd_act.setEnabled(hist.canGoForward())

    def _on_url_changed(self, url: QUrl):
        self.url_bar.setText(url.toString())
        self.url_bar.setCursorPosition(0)
        if not self.incognito:
            if url.toString() not in self.history:
                self.history.append(url.toString())
        self._update_nav_state()

    def new_tab(self, checked: bool = False, url: str = "https://www.google.com"):
        profile = self._create_profile()
        blocker = AdBlocker(self)
        interceptor_method = (
            profile.setUrlRequestInterceptor
            if hasattr(profile, "setUrlRequestInterceptor")
            else profile.setRequestInterceptor
        )
        interceptor_method(blocker)

        view = QWebEngineView(self)
        view.setPage(QWebEnginePage(profile, view))
        view.setUrl(QUrl(url))
        view.urlChanged.connect(self._on_url_changed)
        view.titleChanged.connect(self._update_tab_title)
        profile.downloadRequested.connect(self._handle_download)
        view.loadStarted.connect(lambda: self._toggle_progress(True))
        view.loadProgress.connect(self.progress_value)
        view.loadFinished.connect(self._load_finished)
        self.tabs.addTab(view, "New Tab")
        self.tabs.setCurrentWidget(view)
        self.view = view
        self._tune_settings()

    def close_tab(self, index):
        if self.tabs.count() > 1:
            widget = self.tabs.widget(index)
            if widget:
                widget.deleteLater()
            self.tabs.removeTab(index)

    def tab_changed(self, index):
        self.view = self.tabs.widget(index)
        self._update_nav_state()

    def _update_tab_title(self, title):
        index = self.tabs.indexOf(self.view)
        if index >= 0:
            self.tabs.setTabText(index, title)

    def go_to_url(self):
        url = self.url_bar.text().strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        self.view.setUrl(QUrl(url))

    def browser_home(self):
        self.view.setUrl(QUrl("https://www.google.com"))

    def show_user_agent(self):
        self.status.showMessage(self.view.page().profile().httpUserAgent(), 5000)

    def open_incognito(self):
        Browser(incognito=True).show()

    def _handle_download(self, item):
        filename = item.suggestedFileName()
        dest, _ = QFileDialog.getSaveFileName(self, "Save File", filename)
        if dest:
            if hasattr(item, "setDownloadFileName"):
                item.setDownloadFileName(os.path.basename(dest))
            item.accept(dest)
            self.downloads.append(dest)
            self.status.showMessage(f"Downloading → {dest}", 5000)
        else:
            item.cancel()
            self.status.showMessage("Download canceled", 3000)

    def show_downloads(self):
        dlg = ListDialog("Downloads", self.downloads[::-1])
        if dlg.exec() and (path := dlg.selected_text()):
            if os.path.exists(path):
                os.startfile(path)

    def show_history(self):
        dlg = ListDialog("History", self.history[::-1])
        if dlg.exec() and (url := dlg.selected_text()):
            self.view.setUrl(QUrl(url))

    def show_bookmarks(self):
        dlg = ListDialog("Bookmarks", self.bookmarks[::-1])
        if dlg.exec() and (url := dlg.selected_text()):
            self.view.setUrl(QUrl(url))

    def add_bookmark(self):
        current = self.view.url().toString()
        if current and current not in self.bookmarks:
            self.bookmarks.append(current)
            json.dump(self.bookmarks, open(self.bookmarks_path, "w"))
            QMessageBox.information(self, "Bookmark added", current)

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PySide Browser")
    Browser().show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
