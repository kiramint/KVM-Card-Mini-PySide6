"""Multi-page About dialog: product, authors, thanks, license."""

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
    QStackedWidget,
    QTextBrowser,
    QVBoxLayout,
)

from platform_util import APP_DISPLAY_NAME, apply_resizable_dialog

_HERE = os.path.dirname(os.path.abspath(__file__))

KIRAMINT_URL = "https://github.com/kiramint/"
JACKADMINX_URL = "https://github.com/Jackadminx"
ELLUIFX_URL = "https://github.com/ElluIFX"
ORIGINAL_REPO_URL = "https://github.com/Jackadminx/KVM-Card-Mini"
GROK_URL = "https://x.ai"


def _app_icon() -> QIcon:
    for name in ("icon.icns", "icon.ico"):
        path = os.path.join(_HERE, "icons", name)
        if os.path.isfile(path):
            return QIcon(path)
    return QIcon()


def _browser(html: str) -> QTextBrowser:
    view = QTextBrowser()
    view.setOpenExternalLinks(True)
    view.setReadOnly(True)
    view.setFrameShape(QFrame.NoFrame)
    view.setHtml(html)
    return view


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AboutDialog")
        self.setWindowTitle(f"{self.tr('About')} {APP_DISPLAY_NAME}")

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 12)
        root.setSpacing(12)
        root.addLayout(self._header())

        body = QHBoxLayout()
        body.setSpacing(12)

        self.nav = QListWidget()
        self.nav.setObjectName("aboutNav")
        self.nav.setFixedWidth(128)
        self.nav.setSpacing(2)
        self.nav.setFrameShape(QFrame.NoFrame)
        self.nav.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.nav.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        self.pages = QStackedWidget()
        self.pages.addWidget(_browser(self._about_html()))
        self.pages.addWidget(_browser(self._authors_html()))
        self.pages.addWidget(_browser(self._thanks_html()))
        self.pages.addWidget(_browser(self._license_html()))

        for title in (
            self.tr("About"),
            self.tr("Authors"),
            self.tr("Thanks"),
            self.tr("License"),
        ):
            item = QListWidgetItem(title)
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.nav.addItem(item)

        self.nav.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.nav.setCurrentRow(0)

        body.addWidget(self.nav)
        body.addWidget(self.pages, 1)
        root.addLayout(body, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        root.addWidget(buttons)
        apply_resizable_dialog(
            self,
            min_width=520,
            min_height=360,
            default_width=640,
            default_height=480,
        )

    def _header(self):
        row = QHBoxLayout()
        row.setSpacing(14)

        icon = QLabel()
        pix = _app_icon().pixmap(72, 72)
        if not pix.isNull():
            icon.setPixmap(pix)
            icon.setFixedSize(72, 72)
            row.addWidget(icon, 0, Qt.AlignTop)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        title = QLabel(APP_DISPLAY_NAME)
        title_font = QFont(title.font())
        title_font.setPointSize(max(title_font.pointSize() + 6, 18))
        title_font.setBold(True)
        title.setFont(title_font)

        subtitle = QLabel(self.tr("Simple USB KVM console"))
        subtitle.setWordWrap(True)

        text_col.addWidget(title)
        text_col.addWidget(subtitle)
        text_col.addStretch(1)
        row.addLayout(text_col, 1)
        return row

    def _about_html(self) -> str:
        return (
            "<p>"
            + self.tr(
                "A desktop client that shows the capture-card video and sends "
                "keyboard and mouse over a CH58x vendor HID device."
            )
            + "</p>"
            "<p>"
            + self.tr("This fork runs on Windows, Linux, and macOS.")
            + "</p>"
            "<p>"
            + self.tr("Maintainer:")
            + f' <a href="{KIRAMINT_URL}">https://github.com/kiramint/</a></p>'
        )

    def _authors_html(self) -> str:
        rows = [
            (
                "Jackadminx",
                self.tr("Original project"),
                JACKADMINX_URL,
                self.tr(
                    "Hardware design and the original KVM-Card-Mini host software."
                ),
            ),
            (
                "ElluIFX",
                self.tr("PySide6 rewrite"),
                ELLUIFX_URL,
                self.tr(
                    "Themes, recording, built-in KVM server, paste board, "
                    "and Nuitka packaging."
                ),
            ),
            (
                "kiramint",
                self.tr("This fork"),
                KIRAMINT_URL,
                self.tr(
                    "Cross-platform desktop client for Windows, Linux, and macOS."
                ),
            ),
            (
                "Grok",
                "xAI",
                GROK_URL,
                self.tr(
                    "Assisted with the cross-platform client, packaging, and documentation."
                ),
            ),
        ]
        parts = [f"<p><b>{self.tr('Authors')}</b></p>"]
        for name, role, url, detail in rows:
            parts.append(
                "<p>"
                f"<b>{name}</b> · {role}<br/>"
                f'<a href="{url}">{url}</a><br/>'
                f"{detail}"
                "</p>"
            )
        parts.append(
            "<p>"
            + self.tr("Original repository:")
            + f' <a href="{ORIGINAL_REPO_URL}">{ORIGINAL_REPO_URL}</a></p>'
        )
        return "".join(parts)

    def _thanks_html(self) -> str:
        return (
            "<p><b>"
            + self.tr("Thanks")
            + "</b></p>"
            "<ul>"
            "<li><b>Jackadminx</b> — "
            + self.tr("original hardware and client.")
            + "</li>"
            "<li><b>ElluIFX</b> — "
            + self.tr("PySide6 rewrite and feature set this fork builds on.")
            + "</li>"
            f'<li><b>kiramint</b> — <a href="{KIRAMINT_URL}">https://github.com/kiramint/</a></li>'
            "<li><b>Grok</b> (xAI) — "
            + self.tr("cross-platform client work.")
            + "</li>"
            "<li>Open-IP-KVM — "
            + self.tr("basis of the built-in web KVM server.")
            + "</li>"
            "<li>@wang3076 — "
            + self.tr("WebUSB browser client on the web branch.")
            + "</li>"
            "</ul>"
        )

    def _license_html(self) -> str:
        mit = (
            "Permission is hereby granted, free of charge, to any person obtaining a copy "
            "of this software and associated documentation files (the &quot;Software&quot;), "
            "to deal in the Software without restriction, including without limitation the "
            "rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell "
            "copies of the Software, and to permit persons to whom the Software is furnished "
            "to do so, subject to the following conditions:"
            "<br/><br/>"
            "The above copyright notice and this permission notice shall be included in all "
            "copies or substantial portions of the Software."
            "<br/><br/>"
            "THE SOFTWARE IS PROVIDED &quot;AS IS&quot;, WITHOUT WARRANTY OF ANY KIND, "
            "EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF "
            "MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. "
            "IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, "
            "DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, "
            "ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER "
            "DEALINGS IN THE SOFTWARE."
        )
        return (
            f"<p><b>{self.tr('License')}</b></p>"
            "<p>MIT License</p>"
            "<p>Copyright (c) 2023 Jancgk</p>"
            f"<p>{mit}</p>"
        )
