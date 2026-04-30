"""
Main application window — three-column layout:
  left  : component sidebar (QListWidget)
  centre: scrollable stacked input forms
  right : HTML results panel
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget,
    QLabel, QScrollArea, QTextEdit,
)

from ui.shell_widget import CylindricalShellWidget
from ui.head_widget  import HeadsWidget
from ui.cone_widget  import ConeWidget

# ---------------------------------------------------------------------------
STYLESHEET = """
QWidget {
    background-color: #1e2128;
    color: #e0e0e0;
    font-family: 'Ubuntu', 'Segoe UI', sans-serif;
    font-size: 13px;
}
QGroupBox {
    border: 1px solid #3a3f4b;
    border-radius: 6px;
    margin-top: 8px;
    padding-top: 6px;
    color: #a0b4c8;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}
QLineEdit, QComboBox {
    background-color: #2a2f3a;
    border: 1px solid #3a3f4b;
    border-radius: 4px;
    padding: 4px 8px;
    color: #e0e0e0;
    min-height: 24px;
}
QLineEdit:focus, QComboBox:focus { border: 1px solid #4a9eff; }
QLineEdit:read-only              { color: #80c080; }
QLineEdit:disabled, QComboBox:disabled { color: #505060; }
QPushButton {
    background-color: #1a6bbf;
    color: #ffffff;
    border: none;
    border-radius: 5px;
    padding: 8px 24px;
    font-weight: bold;
    font-size: 13px;
    min-height: 34px;
}
QPushButton:hover   { background-color: #2280d8; }
QPushButton:pressed { background-color: #1155a0; }
QListWidget {
    background-color: #181c24;
    border: none;
    border-right: 1px solid #2a2f3a;
    outline: none;
}
QListWidget::item {
    padding: 11px 16px;
    border-bottom: 1px solid #252b36;
    color: #c0cdd8;
}
QListWidget::item:selected             { background-color: #1a6bbf; color: #ffffff; }
QListWidget::item:hover:!selected      { background-color: #252b36; }
QTabWidget::pane {
    border: 1px solid #3a3f4b;
    border-radius: 4px;
    padding: 4px;
}
QTabBar::tab {
    background-color: #252b36;
    color: #909090;
    padding: 6px 16px;
    border: 1px solid #3a3f4b;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}
QTabBar::tab:selected { background-color: #1a6bbf; color: #ffffff; }
QScrollArea { border: none; background-color: #1e2128; }
QScrollBar:vertical {
    width: 8px;
    background: #1e2128;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #3a3f4b;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QTextEdit {
    background-color: #12151c;
    border: 1px solid #2a2f3a;
    border-radius: 6px;
    padding: 8px;
    font-family: 'Ubuntu Mono', 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    color: #d0d8e0;
}
QCheckBox { color: #c0cdd8; spacing: 6px; }
QCheckBox::indicator {
    width: 15px; height: 15px;
    border: 1px solid #3a3f4b;
    border-radius: 3px;
    background-color: #2a2f3a;
}
QCheckBox::indicator:checked { background-color: #1a6bbf; border-color: #4a9eff; }
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AD-2000 Pressure Vessel Calculator")
        self.setMinimumSize(1100, 650)
        self.resize(1380, 820)
        self.setStyleSheet(STYLESHEET)
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ---- Sidebar ----
        sidebar = QWidget()
        sidebar.setFixedWidth(210)
        sidebar.setStyleSheet("background-color:#181c24;")
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        sb_layout.setSpacing(0)

        title_area = QWidget()
        title_area.setFixedHeight(72)
        ta_layout = QVBoxLayout(title_area)
        ta_layout.setContentsMargins(14, 10, 14, 10)
        lbl_title = QLabel("AD-2000")
        lbl_title.setStyleSheet("color:#4a9eff;font-size:22px;font-weight:bold;")
        lbl_sub   = QLabel("Pressure Vessel Calc.")
        lbl_sub.setStyleSheet("color:#506070;font-size:11px;")
        ta_layout.addWidget(lbl_title)
        ta_layout.addWidget(lbl_sub)

        lbl_section = QLabel("  COMPONENTS")
        lbl_section.setStyleSheet(
            "color:#506070;font-size:10px;font-weight:bold;"
            "background-color:#12151c;padding:8px 0 6px 14px;"
            "letter-spacing:1px;"
        )
        lbl_section.setFixedHeight(28)

        self.component_list = QListWidget()
        for name in [
            "Cylindrical Shell",
            "Hemispherical Head",
            "Ellipsoidal Head (2:1)",
            "Torispherical Head",
            "Flat End Cap",
            "Conical Shell",
        ]:
            self.component_list.addItem(QListWidgetItem(name))
        self.component_list.setCurrentRow(0)
        self.component_list.currentRowChanged.connect(self._switch_component)

        sb_layout.addWidget(title_area)
        sb_layout.addWidget(lbl_section)
        sb_layout.addWidget(self.component_list)

        # ---- Centre: scrollable stacked forms ----
        self.stack = QStackedWidget()

        self._shell_w  = CylindricalShellWidget()
        self._hemi_w   = HeadsWidget("hemispherical")
        self._ellip_w  = HeadsWidget("ellipsoidal")
        self._tori_w   = HeadsWidget("torispherical")
        self._flat_w   = HeadsWidget("flat")
        self._cone_w   = ConeWidget()

        for w in [self._shell_w, self._hemi_w, self._ellip_w,
                  self._tori_w, self._flat_w, self._cone_w]:
            w.result_ready.connect(self._show_result)
            scroll = QScrollArea()
            scroll.setWidget(w)
            scroll.setWidgetResizable(True)
            self.stack.addWidget(scroll)

        # ---- Right: results panel ----
        rp = QWidget()
        rp.setFixedWidth(400)
        rp.setStyleSheet("background-color:#191d25;")
        rp_layout = QVBoxLayout(rp)
        rp_layout.setContentsMargins(10, 12, 10, 10)
        rp_layout.setSpacing(6)

        res_lbl = QLabel("Calculation Results")
        res_lbl.setStyleSheet(
            "color:#4a9eff;font-size:14px;font-weight:bold;padding-bottom:4px;"
        )
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        self.result_display.setPlaceholderText(
            "Results appear here after clicking Calculate.\n\n"
            "Fill in the design parameters and press Calculate."
        )
        rp_layout.addWidget(res_lbl)
        rp_layout.addWidget(self.result_display)

        # Assemble
        root_layout.addWidget(sidebar)
        root_layout.addWidget(self.stack, stretch=1)
        root_layout.addWidget(rp)

    # ------------------------------------------------------------------
    def _switch_component(self, row: int):
        self.stack.setCurrentIndex(row)
        self.result_display.clear()

    def _show_result(self, html: str):
        self.result_display.setHtml(html)
